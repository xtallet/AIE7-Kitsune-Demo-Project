import logging

from lancedb import AsyncConnection, connect_async
from lancedb.table import AsyncTable
from langchain_openai import AzureOpenAIEmbeddings

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class KnowledgeLanceDBAdapter:
    def __init__(
        self,
        db: AsyncConnection,
        table: AsyncTable,
        embedding_model_name: str,
        embedding_client: AzureOpenAIEmbeddings,
    ) -> None:
        self.db = db
        self.table = table
        self.embedding_model_name = embedding_model_name
        self.embedding_client = embedding_client

    @classmethod
    async def create(
        cls,
        db_path: str,
        table_name: str,
        embedding_model_name: str,
        embedding_client: AzureOpenAIEmbeddings,
    ) -> "KnowledgeLanceDBAdapter":
        try:
            db = await connect_async(db_path)
            table = await db.open_table(table_name)
            return cls(db, table, embedding_model_name, embedding_client)
        except Exception as e:
            logging.exception("Failed to initialize LanceDB adapter", e)
            raise

    async def create_embedding(self, text: str) -> list[float]:
        """Async embedding generation."""
        try:
            embedding = await self.embedding_client.aembed_query(text=text)
            return embedding
        except Exception as e:
            logger.exception(f"Failed to create embedding for text: {text}", exc_info=e)
            raise RuntimeError("Failed to create embedding.") from e

    async def search(self, query: str, k: int = 8) -> str:
        """Async vector search."""
        try:
            query_embedding = await self.create_embedding(query)

            search_result = await self.table.search(query_embedding)
            limited = search_result.limit(k)
            df = await limited.to_pandas()

            results = df.drop(columns=["vector", "chunk_id", "_distance"], axis=1)
            formatted_results = await self._format_results(results)

            return formatted_results
        except Exception as e:
            logger.exception(
                f"Failed to search knowledge base for query: {query}",
                exc_info=e,
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
            return formatted
        except Exception as e:
            logger.exception("Failed to format search results", exc_info=e)
            raise RuntimeError("Failed to format search results.") from e

    async def ping(self) -> bool:
        """Test connectivity with the knowledge base by checking if the database connection is open.

        Returns True if the connection is open, otherwise raises an exception.
        """
        try:
            if not self.db.is_open():
                raise RuntimeError("Knowledge base connection is not open.")
            return True
        except Exception as e:
            logger.exception("Knowledge base connectivity test failed", exc_info=e)
            raise RuntimeError(f"Knowledge base connectivity test failed: {str(e)}")
