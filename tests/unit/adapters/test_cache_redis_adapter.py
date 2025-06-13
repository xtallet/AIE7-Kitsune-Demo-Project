import json
from unittest import mock
from unittest.mock import ANY, AsyncMock

import faker
import pytest

from app.adapters.out.cache_redis_adapter import CacheRedisAdapter


class TestCacheRedisAdapter:
    @pytest.fixture(autouse=True)
    @mock.patch("logging.getLogger")
    def setup(self, mock_logger):
        self.adapter = CacheRedisAdapter(
            host="localhost",
            port=6379,
            password="password",
            db=0,
            encoding="utf-8",
        )
        self.mock_logger = mock_logger
        self.faker = faker.Faker()
        self.data = self.faker.json()
        self.key = self.faker.word()

    @pytest.mark.asyncio
    async def test_cache_redis_adapter_save_to_cache(self):
        with mock.patch("redis.asyncio.Redis.set", new_callable=AsyncMock) as mock_set:
            await self.adapter.save_to_cache(self.key, self.data)

        mock_set.assert_called_once_with(self.key, json.dumps(self.data))
        self.mock_logger.return_value.debug.assert_any_call(
            f"Data saved to cache {self.data}"
        )

    @pytest.mark.asyncio
    async def test_cache_redis_adapter_save_to_cache_raise_exception(self):
        with (
            mock.patch(
                "redis.asyncio.Redis.set", new_callable=AsyncMock, side_effect=Exception
            ) as mock_set,
            pytest.raises(Exception),
        ):
            await self.adapter.save_to_cache(self.key, self.data)

        mock_set.assert_called_once_with(self.key, json.dumps(self.data))
        self.mock_logger.return_value.exception.assert_called_once_with(
            f"Failed to save data to cache for key: {self.key}", ANY
        )

    @pytest.mark.asyncio
    async def test_cache_redis_adapter_get_from_cache(self):
        with mock.patch(
            "redis.asyncio.Redis.get",
            new_callable=AsyncMock,
            return_value=json.dumps(self.data),
        ) as mock_get:
            result = await self.adapter.get_from_cache(self.key)

        assert result == self.data
        mock_get.assert_called_once_with(self.key)
        self.mock_logger.return_value.debug.assert_any_call(
            f"Data retrieved from cache: {self.data}"
        )

    @pytest.mark.asyncio
    async def test_cache_redis_adapter_get_from_cache_no_cached(self):
        with mock.patch(
            "redis.asyncio.Redis.get", new_callable=AsyncMock, return_value=None
        ) as mock_get:
            result = await self.adapter.get_from_cache(self.key)

        assert result is None
        mock_get.assert_called_once_with(self.key)
        self.mock_logger.return_value.debug.assert_any_call(
            f"Cache miss for key: {self.key}"
        )

    @pytest.mark.asyncio
    async def test_cache_redis_adapter_get_from_cache_no_cached_json(self):
        with mock.patch(
            "redis.asyncio.Redis.get", new_callable=AsyncMock, return_value=b"asdasd"
        ) as mock_get:
            result = await self.adapter.get_from_cache(self.key)

        assert result is None
        mock_get.assert_called_once_with(self.key)
        self.mock_logger.return_value.error.assert_any_call(
            f"Failed to decode JSON from cache for key: {self.key}"
        )

    @pytest.mark.asyncio
    async def test_cache_redis_adapter_get_from_cache_raise_exception(self):
        with (
            mock.patch(
                "redis.asyncio.Redis.get", new_callable=AsyncMock, side_effect=Exception
            ) as mock_get,
            pytest.raises(Exception),
        ):
            await self.adapter.get_from_cache(self.key)

        mock_get.assert_called_once_with(self.key)
        self.mock_logger.return_value.exception.assert_called_once_with(
            f"Failed to retrieve data from cache for key: {self.key}", ANY
        )

    @pytest.mark.asyncio
    async def test_cache_redis_adapter_ping(self):
        ping_response = self.faker.boolean()

        with mock.patch(
            "redis.asyncio.Redis.ping",
            new_callable=AsyncMock,
            return_value=ping_response,
        ) as mock_ping:
            result = await self.adapter.ping()

        assert result is ping_response
        mock_ping.assert_called_once()
        self.mock_logger.return_value.debug.assert_any_call(
            "Redis cache ping successful."
        )

    @pytest.mark.asyncio
    async def test_cache_redis_adapter_ping_raise_exception(self):
        with (
            mock.patch(
                "redis.asyncio.Redis.ping",
                new_callable=AsyncMock,
                side_effect=Exception,
            ) as mock_ping,
            pytest.raises(RuntimeError),
        ):
            await self.adapter.ping()

        mock_ping.assert_called_once()
        self.mock_logger.return_value.exception.assert_called_once_with(
            "Redis cache connectivity test failed", ANY
        )
