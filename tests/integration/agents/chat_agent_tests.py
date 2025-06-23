import pytest

from app.agents.chat_agent import ChatbotAgent


@pytest.mark.skip(
    "Skipping test for Azure OpenAI due to costs, execute manually when needed."
)
class TestChatbotAgent:
    @pytest.mark.asyncio
    async def test_agent_connection_and_response(self):
        agent = ChatbotAgent()
        result = await agent.run(user_question="How many policies do I have?")

        assert "106" in result
        assert "policies" in result
