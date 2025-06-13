from unittest.mock import AsyncMock, MagicMock

import pytest
from application.chatbot import KitsuneChatbot


class TestKitsuneChatbot:
    @pytest.mark.asyncio
    async def test_get_natural_language_answer(self):
        fake_kitsune_db = MagicMock()
        fake_kitsune_db.run_sql_query = AsyncMock()
        fake_kitsune_db.run_sql_query.return_value = "Results:\ncol1: val1, col2: val2"

        fake_agent = MagicMock()
        fake_agent.run = AsyncMock()
        fake_agent.run.return_value = "Response from agent"

        chatbot = KitsuneChatbot(
            kitsune_db=fake_kitsune_db,
            chatbot_agent=fake_agent,
            llm=MagicMock(),
            cache=MagicMock(),
            knowledge_base=MagicMock(),
            guardrail=MagicMock(),
            logger=MagicMock(),
        )

        result = await chatbot._get_natural_language_answer(
            question="any question", sql_query="any query"
        )

        fake_kitsune_db.run_sql_query.assert_called_once_with(query="any query")
        fake_agent.run.assert_called_once_with(
            user_question="any question",
            context={"sql_answer": "Results:\ncol1: val1, col2: val2"},
        )

        assert result == "Response from agent"

    @pytest.mark.asyncio
    async def test_get_natural_language_answer_exception(self):
        fake_kitsune_db = MagicMock()
        exception = RuntimeError("Database connection error")
        fake_kitsune_db.run_sql_query = AsyncMock(side_effect=exception)

        fake_logger = MagicMock()

        chatbot = KitsuneChatbot(
            kitsune_db=fake_kitsune_db,
            chatbot_agent=MagicMock(),
            llm=MagicMock(),
            cache=MagicMock(),
            knowledge_base=MagicMock(),
            guardrail=MagicMock(),
            logger=fake_logger,
        )

        result = await chatbot._get_natural_language_answer(
            question="any question", sql_query="any query"
        )

        fake_kitsune_db.run_sql_query.assert_called_once_with(query="any query")
        fake_logger.exception.assert_called_once_with(
            "An exception has been raised when executing SQL query", exception
        )

        assert result == "We cannot answer this question right now."
