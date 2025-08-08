from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agno.run.response import RunResponse

from app.agents.chat_agent import ChatbotAgent


class TestChatbotAgent:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.chatbot_agent = ChatbotAgent()

    @pytest.fixture
    def test_data(self):
        return {
            "user_question": "What is the total premium for policy XYZ123?",
            "context": {"sql_result": [{"policy_id": "XYZ123", "premium": 1500}]},
            "user_id": "test_user_123",
            "session_id": "test_session_456",
        }

    @pytest.mark.asyncio
    @patch("app.agents.chat_agent.Agent")
    async def test_run_successful(self, mock_agent_class, test_data):
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response = MagicMock(spec=RunResponse)
        mock_response.content = "The total premium for policy XYZ123 is $1,500."

        mock_agent.arun = AsyncMock(return_value=mock_response)
        mock_agent.session_id = "new_session_id"

        result_content, result_session_id = await self.chatbot_agent.run(
            test_data["user_question"],
            test_data["context"],
            test_data["user_id"],
            test_data["session_id"],
        )

        mock_agent.arun.assert_awaited_once_with(
            message=test_data["user_question"], user_id=test_data["user_id"]
        )

        assert result_content == "The total premium for policy XYZ123 is $1,500."
        assert result_session_id == "new_session_id"

    @pytest.mark.asyncio
    @patch("app.agents.chat_agent.get_storage_db")
    @patch("app.agents.chat_agent.Agent")
    async def test_run_exception(
        self, mock_agent_class, mock_get_storage_db, test_data
    ):
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.arun = AsyncMock(side_effect=Exception("Test error"))

        with pytest.raises(RuntimeError) as excinfo:
            await self.chatbot_agent.run(
                test_data["user_question"],
                test_data["context"],
                test_data["user_id"],
                test_data["session_id"],
            )

        assert "Failed to summarize answer with Agno agent" in str(excinfo.value)
