import json
import gzip
import uuid
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

from app.config.settings import AzureOpenAIConfig
from app.domain.domain import CbotState

logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MONGO_DUMP_PATH = PROJECT_ROOT / "app" / "mongodb" / "kitsune.kitsune.json"

# In-memory index globals
_qdrant_client: QdrantClient | None = None
_embeddings: AzureOpenAIEmbeddings | None = None
_index_built: bool = False
_collection_name = "kitsune_mongo"
_embedding_dim: int | None = None


def iter_json_records(path: Path) -> Iterable[Dict[str, Any]]:
    """
    Yields each JSON object in the file.
    - If the file is a JSON array -> yields each element.
    - Otherwise treats the file as JSON Lines (one JSON object per line).
    - Supports .gz compressed files.
    """
    open_fn = gzip.open if path.suffix == ".gz" else open
    mode = "rt" if path.suffix == ".gz" else "r"

    with open_fn(path, mode, encoding="utf-8") as f:
        # Try to load as a single JSON value first (could be an array)
        try:
            data = json.load(f)
            if isinstance(data, list):
                for obj in data:
                    if isinstance(obj, dict):
                        yield obj
                return
            elif isinstance(data, dict):
                # Single object file (rare for dumps) -> still yield it
                yield data
                return
        except Exception:
            pass

    # If we are here, fallback to JSONL (one object per line)
    with open_fn(path, mode, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, dict):
                yield obj


def safe_get(d: Dict[str, Any], path: str, default=None):
    """
    Safe nested dict access using dot notation.
    Example: safe_get(doc, "data.data.data.policy_id")
    """
    cur = d
    for key in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, default)
        if cur is default:
            return default
    return cur


def flatten_dict(d: Dict[str, Any], prefix: str = "", sep: str = ".", max_depth: int = 6):
    """
    Flatten nested dict into a single-level dict with dot-separated keys.
    Lists are JSON-serialized to avoid explosion of fields.
    """
    out = {}
    if max_depth < 0 or not isinstance(d, dict):
        return out
    for k, v in d.items():
        key = f"{prefix}{sep}{k}" if prefix else str(k)
        if isinstance(v, dict):
            out.update(flatten_dict(v, key, sep=sep, max_depth=max_depth - 1))
        elif isinstance(v, list):
            out[key] = json.dumps(v, ensure_ascii=False)
        else:
            out[key] = v
    return out


def normalize_event(doc: Dict[str, Any]) -> Tuple[str, Dict[str, Any], str]:
    """
    Normalize one MongoDB event document into:
      - oid: stable id (from _id.$oid if present, else random uuid)
      - payload: flat dict with real/derived keys (no invented event_name)
      - text: a human-readable summary good for embeddings
    """
    # 1) stable id
    oid = safe_get(doc, "_id.$oid") or str(uuid.uuid4())

    # 2) Try to get "manifest" (example: "PolicyQuoted")
    manifest = safe_get(doc, "data.manifest")

    # 3) Try a few places where metadata name might appear (some documents duplicate metadata)
    metadata_name = (
        safe_get(doc, "data.data.metadata.name")
        or safe_get(doc, "data.data.data.metadata.name")
        or safe_get(doc, "data.metadata.name")
    )

    # 4) Pick a readable 'name' only if present (we keep both manifest and metadata_name explicit)
    name = manifest or metadata_name or None

    # 5) Choose a reasonable 'deep' payload to flatten.
    #    Common structures in your example: data.data.data  (fall back to data.data, then data)
    deep_candidates = ["data.data.data", "data.data", "data"]
    deep = {}
    for path in deep_candidates:
        cand = safe_get(doc, path)
        if isinstance(cand, dict) and cand:
            deep = dict(cand)  # copy to avoid mutating original
            break

    # 6) Extract commonly used fields from the deep payload (with fallbacks)
    occurred_on = safe_get(deep, "occurred_on") or safe_get(doc, "createdAt.$date") or safe_get(doc, "createdAt")
    policy_id = safe_get(deep, "policy_id")
    if not policy_id:
        # fallback: try top-level "keys" list (example: "policy-<uuid>")
        keys = doc.get("keys")
        if isinstance(keys, list) and len(keys) > 0:
            first = keys[0]
            if isinstance(first, str):
                if first.startswith("policy-"):
                    # strip "policy-" prefix to get the UUID-like id
                    policy_id = first.split("policy-", 1)[-1]
                else:
                    policy_id = first

    # 7) Extract metadata block (aggregate_id, author, ip, event_version)
    meta_block = safe_get(doc, "data.data.metadata") or safe_get(doc, "data.data.data.metadata") or {}
    aggregate_id = meta_block.get("aggregate_id")
    event_version = meta_block.get("event_version")
    author_username = meta_block.get("author_username")
    author_fullname = meta_block.get("author_fullname")
    author_id = meta_block.get("author_id")
    ip = meta_block.get("ip")

    # 8) Remove keys we already extracted from deep before flattening
    for k in ("occurred_on", "policy_id"):
        deep.pop(k, None)

    # 9) Flatten the remaining deep payload under "data.*"
    flat_deep = flatten_dict(deep, prefix="data")

    # 10) Build a compact, human-readable 'text' summary (ideal input for embedding)
    lines = []
    if manifest:
        lines.append(f"Manifest: {manifest}")
    if metadata_name and metadata_name != manifest:
        lines.append(f"Metadata name: {metadata_name}")
    if policy_id:
        lines.append(f"Policy ID: {policy_id}")
    if aggregate_id:
        lines.append(f"Aggregate ID: {aggregate_id}")
    if occurred_on:
        lines.append(f"Occurred on: {occurred_on}")
    if author_fullname or author_username:
        a = author_fullname or ""
        u = author_username or ""
        lines.append(f"Author: {a} ({u})".strip())
    if ip:
        lines.append(f"IP: {ip}")
    if event_version is not None:
        lines.append(f"Event version: {event_version}")
    if safe_get(doc, "createdAt.$date") or safe_get(doc, "createdAt"):
        lines.append(f"Inserted in DB: {safe_get(doc, 'createdAt.$date') or safe_get(doc, 'createdAt')}")

    if flat_deep:
        lines.append("Data details:")
        for k, v in flat_deep.items():
            lines.append(f"  - {k}: {v}")

    text = "\n".join(lines)

    # 11) Assemble payload (only real or clearly-derived keys)
    payload = {
        "mongo_id": oid,
        "manifest": manifest,
        "metadata_name": metadata_name,
        "policy_id": policy_id,
        "aggregate_id": aggregate_id,
        "occurred_on": occurred_on,
        "author_username": author_username,
        "author_fullname": author_fullname,
        "author_id": author_id,
        "ip": ip,
        "event_version": event_version,
        "created_at": safe_get(doc, "createdAt.$date") or safe_get(doc, "createdAt"),
        # keep a 'text' field for embeddings too
        "text": text,
    }
    # Merge flattened deep fields (they are namespaced as data.*)
    payload.update(flat_deep)

    return oid, payload, text


def _ensure_index_built() -> None:
    global _qdrant_client, _embeddings, _index_built, _embedding_dim

    if _index_built:
        return

    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    cfg = AzureOpenAIConfig()

    _qdrant_client = QdrantClient(":memory:")
    _embeddings = AzureOpenAIEmbeddings(
        azure_deployment=cfg.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
        openai_api_version=cfg.AZURE_OPENAI_API_VERSION,
        azure_endpoint=cfg.AZURE_OPENAI_API_ENDPOINT,
        api_key=cfg.AZURE_OPENAI_API_KEY,
    )

    _embedding_dim = len(_embeddings.embed_query("dimension probe"))

    _qdrant_client.recreate_collection(
        collection_name=_collection_name,
        vectors_config=VectorParams(size=_embedding_dim, distance=Distance.COSINE),
    )

    # Load and normalize documents using your notebook's exact logic
    raw_docs = list(iter_json_records(MONGO_DUMP_PATH))
    normalized = [normalize_event(doc) for doc in raw_docs]
    
    # Limit to first 1000 docs for quick local testing
    normalized = normalized[:500]
    
    if not normalized:
        logger.warning("MongoDB dump yielded no documents; index will be empty.")
        _index_built = True
        return

    # Extract texts and payloads
    texts = [text for _, _, text in normalized]
    payloads = [payload for _, payload, _ in normalized]

    # Simple batching for embeddings
    BATCH_SIZE = 64
    vectors: List[List[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        vectors.extend(_embeddings.embed_documents(batch, chunk_size=1024))

    # Upsert points
    points = [
        PointStruct(
            id=hash(oid) % (2**63),
            vector=vec,
            payload=payload,
        )
        for (oid, payload, _), vec in zip(normalized, vectors)
    ]
    _qdrant_client.upsert(collection_name=_collection_name, points=points)

    _index_built = True
    logger.info(f"MongoDB dump indexed in in-memory Qdrant (limited to {len(normalized)} docs).")


async def retriever_mongodb(state: CbotState) -> CbotState:
    """
    Retrieve top-k contexts from the in-memory index built from the MongoDB dump.
    """
    print(f'state.question: {state.question}')
    _ensure_index_built()
    if _qdrant_client is None or _embeddings is None:
        raise RuntimeError("Retriever initialization failed")

    qvec = _embeddings.embed_query(state.question)
    results = _qdrant_client.search(
        collection_name=_collection_name,
        query_vector=qvec,
        limit=5,
    )
    print(f'results: {results}')

    # Extract context strings from the 'text' field in payload
    contexts: List[str] = []
    for r in results:
        payload = r.payload if isinstance(r.payload, dict) else {}
        text = payload.get("text", "")
        if isinstance(text, str) and text.strip():
            contexts.append(text)

    print(f'contexts: {contexts}')
    # Convert list to string for CbotState.context (which expects Optional[str])
    state.context = "\n\n".join(contexts) if contexts else ""
    return state