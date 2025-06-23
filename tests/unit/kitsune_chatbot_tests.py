from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.chatbot import KitsuneChatbot


class TestKitsuneChatbot:
    @pytest.mark.asyncio
    async def test_answer(self):
        fake_logger = MagicMock()

        fake_agent = MagicMock()
        fake_agent.run = AsyncMock()
        fake_agent.run.return_value = "Response from agent"

        cache = MagicMock()
        cache.save_to_cache = AsyncMock()
        cache.get_from_cache = AsyncMock()
        cache.get_from_cache.return_value = None

        guardrail_service = MagicMock()
        guardrail_service.validate_question = AsyncMock()
        guardrail_service.validate_question.return_value = True

        chatbot = KitsuneChatbot(
            chatbot_agent=fake_agent,
            cache=cache,
            guardrail=guardrail_service,
            logger=fake_logger,
        )

        result = await chatbot.answer(question="any question")

        fake_logger.debug.assert_called_once_with(
            "Question: any question.\n Summarized answer: Response from agent"
        )

        cache.get_from_cache.assert_called_once_with("any question")

        cache.save_to_cache.assert_called_once_with(
            "any question",
            {
                "question": "any question",
                "answer": "Response from agent",
            },
        )

        assert result == "Response from agent"
