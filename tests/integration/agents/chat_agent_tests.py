import pytest
from dotenv import load_dotenv
from repositories.chat_agent_repository import ChatAgentRepository

from app.agents.chat_agent import ChatbotAgent

load_dotenv()


@pytest.mark.usefixtures("setup_and_teardown_mongo_db")
class TestChatbotAgent:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.ANY_ID = "123"
        self.chat_agent = ChatbotAgent()

    @pytest.mark.asyncio
    async def test_agent_connection_and_response(self):
        result, session_id = await self.chat_agent.run(
            user_question="How many policies do I have?",
            user_id=self.ANY_ID,
            session_id=self.ANY_ID,
            context={"sql_result": "total_policies, 106"},
        )

        assert "106" in result
        assert "policies" in result
        assert self.ANY_ID == session_id

    @pytest.mark.asyncio
    async def test_check_storage(self):
        await self.chat_agent.run(
            user_question="How many policies do I have?",
            user_id=self.ANY_ID,
            session_id=self.ANY_ID,
            context={"sql_result": "total_policies, 106"},
        )

        agent_session_id = self.chat_agent.agent.session_id
        assert agent_session_id is not None

        repo = ChatAgentRepository()
        last_session = repo.get_last_session(self.ANY_ID)
        assert last_session is not None
        assert last_session["session_id"] == self.ANY_ID

    @pytest.mark.asyncio
    async def test_insert_data_into_database(self):
        user_question = "insert a new policy with the following data: policy_id: 123, policy_name: test, policy_description: test"

        result, _ = await self.chat_agent.run(
            user_question=user_question,
            user_id=self.ANY_ID,
            session_id=self.ANY_ID,
            context={"sql_result": "total_policies, 106"},
        )

        assert result == "I can't perform any action."
