import logging

from lancedb.table import AsyncTable
from openai import AsyncAzureOpenAI

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
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    async def create(cls, db_path, table_name, embedding_model_name, embedding_client):
        try:
            logging.info("Connecting to LanceDB at path: %s", db_path)
            db = await connect_async(db_path)
            table = await db.open_table(table_name)
            logging.info(
                "Successfully connected to LanceDB and opened table: %s", table_name
            )
            return cls(db, table, embedding_model_name, embedding_client)
        except Exception as e:
            logging.error("Failed to initialize LanceDB adapter: %s", str(e))
            raise

    async def create_embedding(self, text: str) -> list[float]:
        """Async embedding generation."""
        try:
            # self.logger.info("Creating embedding for text.")
            response = await self.embedding_client.embeddings.create(
                input=[text], model=self.embedding_model_name
            )
            embedding = response.data[0].embedding
            self.logger.debug("Generated embedding: %s", embedding)
            return embedding
        except Exception as e:
            self.logger.error(
                "Failed to create embedding for text: %s, Error: %s", text, str(e)
            )
            raise RuntimeError("Failed to create embedding.") from e

    async def search(self, query: str, k: int = 8, drop_columns: bool = True) -> str:
        """Async vector search."""
        try:
            # self.logger.info("Searching knowledge base with query: %s", query)
            query_embedding = await self.create_embedding(query)
            self.logger.debug("Query embedding: %s", query_embedding)

            search_result = await self.table.search(query_embedding)
            limited = search_result.limit(k)
            df = await limited.to_pandas()
            self.logger.debug("Search results dataframe: %s", df)

            if drop_columns:
                results = df.drop(columns=["vector", "chunk_id", "_distance"], axis=1)
            else:
                results = df
            formatted_results = await self._format_results(results)
            return formatted_results
        except Exception as e:
            self.logger.error(
                "Failed to search knowledge base for query: %s, Error: %s",
                query,
                str(e),
            )
            raise RuntimeError("Failed to search knowledge base.") from e

    async def _format_results(self, results):
        try:
            self.logger.info("Formatting search results.")
            formatted = "\n\n".join(
                f"question: {row['question']}\n"
                f"cot: {row['cot']}\n"
                f"sql_query: {row['sql_query']}"
                for _, row in results.iterrows()
            )
            self.logger.debug("Formatted results: %s", formatted)
            return formatted
        except Exception as e:
            self.logger.error("Failed to format search results: %s", str(e))
            raise RuntimeError("Failed to format search results.") from e

    async def ping(self) -> bool:
        """Test connectivity with the knowledge base by checking if the database connection is open.

        Returns True if the connection is open, otherwise raises an exception.
        """
        try:
            if not self.db.is_open():
                raise RuntimeError("Knowledge base connection is not open.")
            self.logger.info("Knowledge base ping successful.")
            return True
        except Exception as e:
            self.logger.exception("Knowledge base connectivity test failed", e)
            raise RuntimeError(f"Knowledge base connectivity test failed: {str(e)}")
