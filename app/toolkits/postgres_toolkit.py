import logging

from agno.exceptions import StopAgentRun
from agno.tools import tool
from agno.tools.postgres import PostgresTools

from app.config.settings import KitsuneDBConfig, ToolkitCacheConfig

postgres_logger = logging.getLogger("postgres_toolkit")
postgres_logger.setLevel(logging.INFO)
toolkit_cache_config = ToolkitCacheConfig()


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


@tool(
    name="postgres_toolkit",
    description="Run a query against the PostgreSQL database",
    show_result=True,
    cache_results=toolkit_cache_config.TOOLKIT_CACHE_ENABLED,
    cache_ttl=toolkit_cache_config.TOOLKIT_CACHE_TTL,
    cache_dir="/tmp/postgres_toolkit_cache",
)
def postgres_toolkit(query: str):
    try:
        postgres_logger.info(f"Running query: {query}")
        result = _get_postgres_tools().run_query(query)
        postgres_logger.info(f"Query result: {result}")
        return result

    except Exception as e:
        postgres_logger.exception("Failed to run query", e)
        raise StopAgentRun(f"Failed to run query: {str(e)}")
