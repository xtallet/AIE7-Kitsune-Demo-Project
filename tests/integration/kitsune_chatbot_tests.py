from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv

from app.adapters.out.adapter_factory import (
    build_cache_adapter,
    build_guardrail_adapter,
)
from app.agents.chat_agent import ChatbotAgent
from app.application.chatbot import KitsuneChatbot

load_dotenv()


@pytest.mark.skip(
    "Skipping test for Azure OpenAI due to costs, execute manually when needed."
)
class TestKitsuneChatbot:
    @pytest.mark.asyncio
    async def test_answer(self):
        fake_logger = MagicMock()
        chatbot = KitsuneChatbot(
            cache=build_cache_adapter(),
            guardrail=build_guardrail_adapter(),
            logger=fake_logger,
            chatbot_agent=ChatbotAgent(),
        )

        response, session_id = await chatbot.answer(
            "How many policies do I have?", user_id=self.test_user_id
        )

        assert response is not None
        assert "106" in response
        assert "policies" in response
        assert session_id is not None

    @pytest.mark.asyncio
    async def test_answer_with_session_id(self):
        fake_logger = MagicMock()
        chatbot = KitsuneChatbot(
            cache=build_cache_adapter(),
            guardrail=build_guardrail_adapter(),
            logger=fake_logger,
            chatbot_agent=ChatbotAgent(),
        )

        user_session_id = "123"

        response, session_id = await chatbot.answer(
            "How many policies do I have?",
            user_id=self.test_user_id,
            session_id=user_session_id,
        )

        assert response is not None
        assert "106" in response
        assert "policies" in response
        assert session_id is not None
        assert session_id == user_session_id
