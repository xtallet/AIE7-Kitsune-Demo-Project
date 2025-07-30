import os
import urllib.parse
from functools import cached_property
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class AzureOpenAIConfig(BaseSettings):
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_API_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_LLM_MODEL: str
    AZURE_OPENAI_LLM_DEPLOYMENT_NAME: str
    AZURE_OPENAI_EMBEDDING_MODEL: str
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str


class RedisConfig(BaseSettings):
    REDIS_ENABLE_FLAG: bool = True
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DB: int = 0
    REDIS_ENCODING: str = "utf8"

    @field_validator("REDIS_ENABLE_FLAG", mode="before")
    @classmethod
    def parse_redis_enable_flag(cls, value: Any) -> bool:
        if isinstance(value, str):
            return value.lower() in {"true", "1", "yes"}
        return bool(value)

    @field_validator("REDIS_PORT", "REDIS_DB", mode="before")
    @classmethod
    def parse_int_fields(cls, value: Any) -> int:
        if isinstance(value, str):
            return int(value)
        return value


class LanceDBConfig(BaseSettings):
    LANCEDB_PATH: str
    LANCEDB_TABLE_NAME: str
    LANCEDB_EMBEDDING_MODEL: str


class KitsuneDBConfig(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SCHEMA: str

    @cached_property
    def postgres_host(self) -> str:
        """Return localhost as the host when in test mode, otherwise the configured host."""
        if bool(os.getenv("TEST_RUN", False)) is True:
            return "localhost"
        return self.POSTGRES_HOST


class ToolkitCacheConfig(BaseSettings):
    TOOLKIT_CACHE_ENABLED: bool = True
    TOOLKIT_CACHE_TTL: int = 3600


class GuardrailConfig(BaseSettings):
    ALLOWED_TOPICS: Any

    @field_validator("ALLOWED_TOPICS", mode="before")
    @classmethod
    def parse_allowed_topics(cls, value: str) -> List[str]:
        if isinstance(value, str):
            return [topic.strip() for topic in value.split(",")]
        return value


class MongoDBConfig(BaseSettings):
    MONGODB_HOST: str
    MONGODB_USERNAME: str
    MONGODB_PASSWORD: str
    MONGODB_PROTOCOL: str = "mongodb"

    @cached_property
    def connection_string(self) -> str:
        connection_string = f"{self.MONGODB_PROTOCOL}://"
        connection_string = f"{connection_string}{urllib.parse.quote_plus(self.MONGODB_USERNAME)}:{urllib.parse.quote_plus(self.MONGODB_PASSWORD)}@{self.mongodb_host}"
        return connection_string

    @cached_property
    def mongodb_host(self) -> str:
        """Return localhost as the host when in test mode, otherwise the configured host."""
        if bool(os.getenv("TEST_RUN", False)) is True:
            return "localhost"
        return self.MONGODB_HOST
