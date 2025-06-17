import json
import logging
from typing import Any

import redis.asyncio as redis

from app.domain.ports.cache_port import Cache


class NoOpCacheAdapter(Cache):
    async def save_to_cache(self, key: str, data: Any) -> None:
        pass

    async def get_from_cache(self, key: str) -> Any:
        return None

    async def ping(self) -> bool:
        return True


class CacheRedisAdapter(Cache):
    def __init__(
        self,
        host: str,
        port: int,
        password: str,
        db: int,
        encoding: str,
    ):
        self.client = redis.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True,
            db=db,
            encoding=encoding,
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    async def save_to_cache(self, key: str, data: Any) -> None:
        try:
            await self.client.set(key, json.dumps(data))
            self.logger.debug(f"Data saved to cache {data}")
        except Exception as e:
            self.logger.exception(f"Failed to save data to cache for key: {key}", e)
            raise

    async def get_from_cache(self, key: str) -> Any:
        try:
            value = await self.client.get(key)
            if not value:
                self.logger.debug(f"Cache miss for key: {key}")
                return None
            data = json.loads(value)
            self.logger.debug(f"Data retrieved from cache: {data}")
            return data
        except json.JSONDecodeError as e:
            self.logger.exception(f"Failed to decode JSON from cache for key: {key}", e)
            return None
        except Exception as e:
            self.logger.exception(
                f"Failed to retrieve data from cache for key: {key}", e
            )
            raise

    async def ping(self) -> bool:
        """Test connectivity with the Redis cache by sending a PING command.

        Returns True if the Redis server responds successfully, otherwise raises an exception.
        """
        try:
            response = await self.client.ping()
            self.logger.debug("Redis cache ping successful.")
            return response
        except Exception as e:
            self.logger.exception("Redis cache connectivity test failed", e)
            raise RuntimeError(f"Redis cache connectivity test failed: {str(e)}")
