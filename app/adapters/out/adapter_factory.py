import logging

from agno.models.azure import AzureOpenAI
from openai import AsyncAzureOpenAI, Embedding

from app.adapters.out.agent_adapter import ChatbotAgentAdapter
from app.adapters.out.sql_agent_adapter import SQLAgentAdapter
from app.adapters.out.cache_redis_adapter import CacheRedisAdapter, NoOpCacheAdapter
from app.adapters.out.guardrail_adapter import GuardrailAdapter
from app.adapters.out.knowledge_lancedb_adapter import KnowledgeLanceDBAdapter
from app.adapters.out.postgres_toolkit_factory import PostgresToolkitFactory
from app.adapters.out.sql_agent_adapter import SQLAgentAdapter
from app.config.settings import (
    AzureOpenAIConfig,
    GuardrailConfig,
    LanceDBConfig,
    RedisConfig,
)


def build_cache_adapter():
    redis_config = RedisConfig()

    if not redis_config.REDIS_ENABLE_FLAG:
        logging.getLogger(__name__).info(
            "Redis cache is disabled, using NoOpCacheAdapter."
        )
        return NoOpCacheAdapter()

    return CacheRedisAdapter(
        host=redis_config.REDIS_HOST,
        port=redis_config.REDIS_PORT,
        password=redis_config.REDIS_PASSWORD,
        db=redis_config.REDIS_DB,
        encoding=redis_config.REDIS_ENCODING,
    )


def build_azure_openai_client() -> Embedding:
    azure_config = AzureOpenAIConfig()
    return AsyncAzureOpenAI(
        api_key=azure_config.AZURE_OPENAI_API_KEY,
        api_version=azure_config.AZURE_OPENAI_API_VERSION,
        azure_endpoint=azure_config.AZURE_OPENAI_API_ENDPOINT,
    )


def build_knowledge_base_adapter():
    lancedb_config = LanceDBConfig()
    return KnowledgeLanceDBAdapter.create(
        db_path=lancedb_config.LANCEDB_PATH,
        table_name=lancedb_config.LANCEDB_TABLE_NAME,
        embedding_model_name=lancedb_config.LANCEDB_EMBEDDING_MODEL,
        embedding_client=build_azure_openai_client(),
    )


def build_db_toolkit():
    return PostgresToolkitFactory()


def build_guardrail_adapter():
    guardrail_config = GuardrailConfig()
    azure_config = AzureOpenAIConfig()
    return GuardrailAdapter(
        model_name=azure_config.AZURE_OPENAI_LLM_MODEL,
        azure_deployment=azure_config.AZURE_OPENAI_LLM_DEPLOYMENT_NAME,
        azure_endpoint=azure_config.AZURE_OPENAI_API_ENDPOINT,
        api_version=azure_config.AZURE_OPENAI_API_VERSION,
        api_key=azure_config.AZURE_OPENAI_API_KEY,
        allowed_topics=guardrail_config.ALLOWED_TOPICS,
    )


def build_agent():
    azure_config = AzureOpenAIConfig()
    return ChatbotAgentAdapter(
        model=AzureOpenAI(azure_config.AZURE_OPENAI_LLM_DEPLOYMENT_NAME),
    )


async def build_sql_agent():
    azure_config = AzureOpenAIConfig()
    postgres_toolkit = PostgresToolkitFactory().get_db_tools()
    return SQLAgentAdapter(
        model=AzureOpenAI(azure_config.AZURE_OPENAI_LLM_DEPLOYMENT_NAME),
        postgres_toolkit=postgres_toolkit,
    )
