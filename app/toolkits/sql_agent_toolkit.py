import logging

from agno.tools import tool

from app.adapters.out.adapter_factory import build_knowledge_base_adapter
from app.agents.sql_agent import SQLAgent
from app.config.settings import ToolkitCacheConfig

sql_agent_logger = logging.getLogger("sql_agent_toolkit")

toolkit_cache_config = ToolkitCacheConfig()


@tool(
    name="sql_agent",
    description="Generate an SQL and execute it",
    show_result=True,
    cache_results=toolkit_cache_config.TOOLKIT_CACHE_ENABLED,
    cache_ttl=toolkit_cache_config.TOOLKIT_CACHE_TTL,
    cache_dir="/tmp/sql_agent_cache",
)
async def sql_agent_toolkit(user_question: str):
    """Use this function to get the information from the database.

    Args:
        user_question (str): The user question to ask the database.

    Returns:
        str: JSON string of the information from the database.
    """
    try:
        lancedb_adapter = await build_knowledge_base_adapter()
        context = await lancedb_adapter.search(query=user_question)
        agent = SQLAgent(context)

        result = await agent.run(user_question=user_question)
    except Exception as e:
        sql_agent_logger.exception("Failed to get context from LanceDB adapter", e)
        return "Could not retreive the requested information from the database"

    return result
