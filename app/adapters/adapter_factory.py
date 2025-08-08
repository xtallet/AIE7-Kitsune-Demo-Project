import logging

from langchain_openai import AzureOpenAIEmbeddings

from app.adapters.cache_redis_adapter import CacheRedisAdapter, NoOpCacheAdapter
from app.adapters.guardrail_adapter import GuardrailAdapter
from app.adapters.knowledge_lancedb_adapter import KnowledgeLanceDBAdapter
from app.adapters.llm_adapter import LLMAdapter
from app.config.settings import (
    AzureOpenAIConfig,
    GuardrailConfig,
    LanceDBConfig,
    RedisConfig,
)


def build_cache_adapter() -> CacheRedisAdapter | NoOpCacheAdapter:
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


async def build_knowledge_base_adapter() -> KnowledgeLanceDBAdapter:
    lancedb_config = LanceDBConfig()
    azure_config = AzureOpenAIConfig()
    return await KnowledgeLanceDBAdapter.create(
        db_path=lancedb_config.LANCEDB_PATH,
        table_name=lancedb_config.LANCEDB_TABLE_NAME,
        embedding_model_name=lancedb_config.LANCEDB_EMBEDDING_MODEL,
        embedding_client=AzureOpenAIEmbeddings(
            azure_endpoint=azure_config.AZURE_OPENAI_API_ENDPOINT,
            azure_deployment=azure_config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
            openai_api_version=azure_config.AZURE_OPENAI_API_VERSION,
        ),
    )


def build_guardrail_adapter() -> GuardrailAdapter:
    guardrail_config = GuardrailConfig()
    azure_config = AzureOpenAIConfig()
    return GuardrailAdapter(
        model_name=azure_config.AZURE_OPENAI_LLM_MODEL,
        azure_deployment=azure_config.AZURE_OPENAI_LLM_DEPLOYMENT_NAME,
        azure_endpoint=azure_config.AZURE_OPENAI_API_ENDPOINT,
        api_version=azure_config.AZURE_OPENAI_API_VERSION,
        allowed_topics=guardrail_config.ALLOWED_TOPICS,
    )


def build_llm_adapter() -> LLMAdapter:
    azure_config = AzureOpenAIConfig()
    return LLMAdapter(
        model_name=azure_config.AZURE_OPENAI_LLM_MODEL,
        azure_deployment=azure_config.AZURE_OPENAI_LLM_DEPLOYMENT_NAME,
        azure_endpoint=azure_config.AZURE_OPENAI_API_ENDPOINT,
        api_version=azure_config.AZURE_OPENAI_API_VERSION,
    )
