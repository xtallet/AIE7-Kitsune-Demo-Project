import json
import logging
from typing import Any, Optional

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
        client: Optional[redis.Redis] = None,
    ):
        self.client = client or redis.Redis(
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
            # self.logger.info("Saving data to cache with key: %s", key)
            await self.client.set(key, json.dumps(data))
            self.logger.debug("Data saved to cache: %s", data)
        except Exception as e:
            self.logger.error(
                "Failed to save data to cache for key: %s, Error: %s", key, str(e)
            )
            raise

    async def get_from_cache(self, key: str) -> Any:
        try:
            # self.logger.info("Retrieving data from cache with key: %s", key)
            value = await self.client.get(key)
            if not value:
                self.logger.debug("Cache miss for key: %s", key)
                return None
            data = json.loads(value)
            self.logger.debug("Data retrieved from cache: %s", data)
            return data
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON from cache for key: %s", key)
            return None
        except Exception as e:
            self.logger.error(
                "Failed to retrieve data from cache for key: %s, Error: %s", key, str(e)
            )
            raise

    async def ping(self) -> bool:
        """Test connectivity with the Redis cache by sending a PING command.

        Returns True if the Redis server responds successfully, otherwise raises an exception.
        """
        try:
            response = await self.client.ping()
            self.logger.info("Redis cache ping successful.")
            return response
        except Exception as e:
            self.logger.exception("Redis cache connectivity test failed", e)
            raise RuntimeError(f"Redis cache connectivity test failed: {str(e)}")
