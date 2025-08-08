import logging

from agno.exceptions import StopAgentRun
from agno.tools.postgres import PostgresTools

from app.config.settings import KitsuneDBConfig

postgres_logger = logging.getLogger()
postgres_logger.setLevel(logging.INFO)


def _get_postgres_tools() -> PostgresTools:
    config = KitsuneDBConfig()
    return PostgresTools(
        host=config.postgres_host,
        port=config.POSTGRES_PORT,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
        db_name=config.POSTGRES_DB,
        table_schema=config.POSTGRES_SCHEMA,
    )


def postgres_toolkit(query: str) -> str:
    try:
        postgres_logger.info(f"Running query: {query}")
        result = _get_postgres_tools().run_query(query)
        postgres_logger.info(f"Query result: {result}")
        return result

    except Exception as e:
        postgres_logger.exception("Failed to run query", e)
        raise StopAgentRun(f"Failed to run query: {str(e)}")
