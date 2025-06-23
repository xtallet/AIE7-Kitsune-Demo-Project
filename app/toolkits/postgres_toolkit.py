import logging

from agno.tools import tool
from agno.tools.postgres import PostgresTools

from app.config.settings import KitsuneDBConfig, ToolkitCacheConfig

postgres_logger = logging.getLogger("postgres_toolkit")

toolkit_cache_config = ToolkitCacheConfig()


@tool(
    name="postgres_toolkit",
    description="Run a query against the PostgreSQL database",
    show_result=True,
    cache_results=toolkit_cache_config.TOOLKIT_CACHE_ENABLED,
    cache_ttl=toolkit_cache_config.TOOLKIT_CACHE_TTL,
    cache_dir="/tmp/postgres_toolkit_cache",
)
def postgres_toolkit(query: str):
    config = KitsuneDBConfig()

    postgres_logger.info(f"Running query: {query}")

    return PostgresTools(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
        db_name=config.POSTGRES_DB,
        table_schema=config.POSTGRES_SCHEMA,
    ).run_query(query)
