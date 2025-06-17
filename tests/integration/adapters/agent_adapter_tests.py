import os

import pytest
from agno.models.azure import AzureOpenAI
from dotenv import load_dotenv

from app.adapters.out.agent_adapter import ChatbotAgentAdapter

load_dotenv()


@pytest.mark.skip(
    "Skipping test for Azure OpenAI due to costs, execute manually when needed."
)
class TestChatbotAgent:
    @pytest.mark.asyncio
    async def test_agent_connection_and_response(self):

        agent = ChatbotAgentAdapter(
            AzureOpenAI(os.getenv("AZURE_OPENAI_LLM_TESTING_DEPLOYMENT_NAME")),
        )
        result = await agent.run(
            user_question="How many policies do I have?", context={"sql_answer": "3"}
        )

        assert "3" in result
        assert "policies" in result
