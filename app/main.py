import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import aiohttp
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from app.adapters.adapter_factory import (
    build_cache_adapter,
    build_knowledge_base_adapter,
)
from app.application.graph import compile_graph
from app.config.settings import LangSmithConfig
from app.domain.domain import CbotState
from app.repositories.chat_agent_repository import ChatAgentRepository
from app.toolkits.postgres_toolkit import _get_postgres_tools

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str]
    question: str

    @field_validator("question")
    def validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be empty or whitespace")
        return value


async def _lifespan() -> List[str]:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    service_errors = []

    # Test Redis cache connectivity
    cache_adapter = build_cache_adapter()
    if not await cache_adapter.ping():
        service_errors.append("Redis cache connectivity test failed.")

    # Test LanceDB connectivity
    lancedb_adapter = await build_knowledge_base_adapter()
    if not await lancedb_adapter.ping():
        service_errors.append("Knowledge DB connection is not open.")

    # Test MongoDB connectivity
    chat_agent_repo = ChatAgentRepository()
    if not await chat_agent_repo.ping():
        service_errors.append("MongoDB connectivity test failed.")

    # Test Postgres connectivity
    tool = _get_postgres_tools()
    result = tool.run_query(
        "SELECT COUNT(cp.policy_reference) AS total_policies FROM get_premiums() cp;"
    )
    if not result or "Error" in result:
        service_errors.append("Postgres connectivity test failed.")

    # Test LangSmith connectivity
    try:
        langsmith_config = LangSmithConfig()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{langsmith_config.LANGSMITH_ENDPOINT}/api/v1/info",
                headers={
                    "Authorization": f"Bearer {langsmith_config.LANGSMITH_API_KEY}"
                },
            ) as response:
                if response.status >= 400:
                    raise Exception(f"HTTP error {response.status}")
                await response.text()  # Ensure we read the response
    except Exception as e:
        error_msg = f"LangSmith connectivity test failed: {str(e)}"
        service_errors.append(error_msg)
        logger.error(error_msg)

    return service_errors


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    service_errors = await _lifespan()

    if service_errors:
        logger.error("\n".join(service_errors))
        raise RuntimeError(f"Checks failed: {'; '.join(service_errors)}")
    else:
        yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class ChatbotService:
    def __init__(self):
        self.agent = None
        self._initialized = False
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger("fastapi")
        self.logger.setLevel(logging.INFO)

    async def _async_init(self):
        if not self._initialized:
            async with self._lock:
                if not self._initialized:  # Double-check inside the lock
                    logger.info("Compiling Graph...")
                    self.compiled_graph = await compile_graph()
                    self._initialized = True
                    logger.info("Graph Compiled.")

    async def answer(
        self, question: str, user_id: str, session_id: Optional[str] = None
    ) -> Tuple[str, str]:
        await self._async_init()
        state = CbotState(question=question, user_id=user_id, session_id=session_id)
        result = await self.compiled_graph.ainvoke(state)
        return result["answer"], result["session_id"]


chatbot_service = ChatbotService()


@app.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    response, session_id = await chatbot_service.answer(
        request.question, request.user_id, request.session_id
    )
    return {"response": response, "session_id": session_id}


@app.get("/readiness")
async def readiness():
    service_errors = await _lifespan()

    if service_errors:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not ready", "errors": service_errors},
        )

    return {"status": "ready"}


@app.get("/liveness")
async def liveness():
    return {"status": "alive"}
