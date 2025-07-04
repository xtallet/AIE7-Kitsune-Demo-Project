import pytest
from dotenv import load_dotenv
from repositories.chat_agent_repository import ChatAgentRepository

from app.agents.chat_agent import ChatbotAgent

load_dotenv()


@pytest.mark.skip(
    "Skipping test for Azure OpenAI due to costs, execute manually when needed."
)
class TestChatbotAgent:
    @pytest.mark.asyncio
    async def test_agent_connection_and_response(self):
        agent = ChatbotAgent()
        session_id = "123"

        result = await agent.run(
            user_question="How many policies do I have?",
            user_id=self.test_user_id,
            session_id=session_id,
        )

        assert "106" in result
        assert "policies" in result

    @pytest.mark.asyncio
    async def test_check_storage(self):
        agent = ChatbotAgent()
        user_question = "How many policies do I have?"
        session_id = "123"

        result = await agent.run(
            user_question=user_question,
            user_id=self.test_user_id,
            session_id=session_id,
        )

        assert "106" in result
        assert "policies" in result

        agent_session_id = agent.agent.session_id
        assert agent_session_id is not None

        repo = ChatAgentRepository()
        last_session = repo.get_last_session(self.test_user_id)
        assert last_session is not None
        assert last_session["session_id"] == session_id
