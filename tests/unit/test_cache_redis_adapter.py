from unittest.mock import MagicMock

from app.adapters.out.cache_redis_adapter import CacheRedisAdapter
from app.application.chatbot import KitsuneChatbot
from tests.fakes.fake_factory import (
    FakeCache,
    FakeKitsuneDB,
    FakeKnowledgeBase,
    FakeLLM,
)


def test_cache_redis_adapter_save_to_cache():
    mock_redis = MagicMock()
    adapter = CacheRedisAdapter(client=mock_redis)
    adapter.save_to_cache("key", {"data": "value"})
    mock_redis.set.assert_called_once_with("key", '{"data": "value"}')


def test_cache_redis_adapter_get_from_cache():
    mock_redis = MagicMock()
    mock_redis.get.return_value = '{"data": "value"}'
    adapter = CacheRedisAdapter(client=mock_redis)
    result = adapter.get_from_cache("key")
    assert result == {"data": "value"}
    mock_redis.get.assert_called_once_with("key")


def test_chatbot_returns_cached_answer():
    fake_cache = FakeCache()
    fake_knowledge_base = FakeKnowledgeBase()
    fake_kitsune_db = FakeKitsuneDB()
    fake_llm = FakeLLM()

    fake_cache.save_to_cache("hi", {"answer": "hello!"})
    bot = KitsuneChatbot(
        cache=fake_cache,
        knowledge_base=fake_knowledge_base,
        kitsune_db=fake_kitsune_db,
        llm=fake_llm,
    )
    assert bot.answer("hi") == "hello!"
