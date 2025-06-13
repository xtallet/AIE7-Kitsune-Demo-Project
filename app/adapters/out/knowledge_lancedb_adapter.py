import logging

from lancedb.table import AsyncTable
from openai import AsyncAzureOpenAI, Embedding

from app.domain.ports.knowledge_base_port import KnowledgeBase
from lancedb import AsyncConnection, connect_async


class KnowledgeLanceDBAdapter(KnowledgeBase):
    def __init__(
        self,
        db: AsyncConnection,
        table: AsyncTable,
        embedding_model_name: str,
        embedding_client: AsyncAzureOpenAI,
    ) -> None:
        self.db = db
        self.table = table
        self.embedding_model_name = embedding_model_name
        self.embedding_client = embedding_client
        self.logger = logging.getLogger(__name__)

    @classmethod
    async def create(
        cls,
        db_path: str,
        table_name: str,
        embedding_model_name: str,
        embedding_client: Embedding,
    ):
        try:
            db = await connect_async(db_path)
            table = await db.open_table(table_name)
            logging.info(
                f"Successfully connected to LanceDB and opened table: {table_name}"
            )
            return cls(db, table, embedding_model_name, embedding_client)
        except Exception as e:
            logging.exception("Failed to initialize LanceDB adapter", e)
            raise

    async def create_embedding(self, text: str) -> list[float]:
        """Async embedding generation."""
        try:
            response = await self.embedding_client.embeddings.create(
                input=[text], model=self.embedding_model_name
            )
            embedding = response.data[0].embedding
            self.logger.debug(f"Generated embedding: {embedding}")
            return embedding
        except Exception as e:
            self.logger.exception(f"Failed to create embedding for text: {text}", e)
            raise RuntimeError("Failed to create embedding.") from e

    async def search(self, query: str, k: int = 8) -> str:
        """Async vector search."""
        try:
            query_embedding = await self.create_embedding(query)
            self.logger.debug(f"Query embedding: {query_embedding}")

            search_result = await self.table.search(query_embedding)
            limited = search_result.limit(k)
            df = await limited.to_pandas()
            self.logger.debug(f"Search results dataframe: {df}")

            results = df.drop(columns=["vector", "chunk_id", "_distance"], axis=1)
            formatted_results = await self._format_results(results)

            return formatted_results
        except Exception as e:
            self.logger.exception(
                f"Failed to search knowledge base for query: {query}",
                e,
            )
            raise RuntimeError("Failed to search knowledge base.") from e

    async def _format_results(self, results):
        try:
            formatted = "\n\n".join(
                f"question: {row['question']}\n"
                f"cot: {row['cot']}\n"
                f"sql_query: {row['sql_query']}"
                for _, row in results.iterrows()
            )
            self.logger.debug("Formatted results: %s", formatted)
            return formatted
        except Exception as e:
            self.logger.exception("Failed to format search results", e)
            raise RuntimeError("Failed to format search results.") from e

    async def ping(self) -> bool:
        """Test connectivity with the knowledge base by checking if the database connection is open.

        Returns True if the connection is open, otherwise raises an exception.
        """
        try:
            if not self.db.is_open():
                raise RuntimeError("Knowledge base connection is not open.")
            self.logger.debug("Knowledge base ping successful.")
            return True
        except Exception as e:
            self.logger.exception("Knowledge base connectivity test failed", e)
            raise RuntimeError(f"Knowledge base connectivity test failed: {str(e)}")
