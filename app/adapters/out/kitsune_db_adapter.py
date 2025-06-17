import logging
from typing import Any, List

from psycopg import AsyncConnection

from app.domain.ports.kitsune_db_port import KitsuneDB


class KitsuneDBAdapter(KitsuneDB):

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db_name: str,
        db_schema: str,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.db_schema = db_schema
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _get_kitsune_db_client(self) -> AsyncConnection:
        try:
            return await AsyncConnection.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.db_name,
            )
        except Exception as e:
            self.logger.exception("Failed to connect to the database", e)
            raise RuntimeError("Failed to connect to the database.") from e

    async def _format_results_as_string(
        self, results: List[tuple], columns: List[str]
    ) -> str:
        formatted_result = "Results:\n"
        for row in results:
            formatted_result += (
                ", ".join(f"{col}: {val}" for col, val in zip(columns, row)) + "\n"
            )
        return formatted_result.strip()

    async def run_sql_query(self, query: str) -> Any:
        try:
            conn = await self._get_kitsune_db_client()
            async with conn.cursor() as cursor:
                await cursor.execute(f"SET search_path TO {self.db_schema};")
                self.logger.debug(f"Search path set to schema: {self.db_schema}")
                await cursor.execute(query)
                results = await cursor.fetchall()
                columns = [desc.name for desc in cursor.description]
                self.logger.debug(f"Query results: {results}")
            await conn.close()
            return await self._format_results_as_string(results, columns)
        except Exception as e:
            self.logger.exception(
                f"An error occurred while executing the SQL query: {query}", e
            )
            raise RuntimeError(
                "An error occurred while executing the SQL query."
            ) from e

    async def ping(self) -> bool:
        """Test connectivity with the database by executing a simple query.

        Returns True if the query executes successfully, otherwise raises an exception.
        """
        try:
            conn = await self._get_kitsune_db_client()
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1;")
                result = await cursor.fetchone()
                self.logger.debug("Database ping successful.")
            await conn.close()
            return result is not None
        except Exception as e:
            self.logger.exception("Database connectivity test failed", e)
            raise RuntimeError(f"Database connectivity test failed: {str(e)}")
