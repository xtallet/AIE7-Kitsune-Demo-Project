import logging
from typing import Optional

from agents.memory import get_storage_db
from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.run.response import RunResponse

from app.agents.agent_port import AgentInterface
from app.config.settings import AzureOpenAIConfig
from app.toolkits.sql_agent_toolkit import sql_agent_toolkit


class ChatbotAgent(AgentInterface):
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.azureOpenAiconfig = AzureOpenAIConfig()
        self.sql_agent_toolkit = sql_agent_toolkit

    def _init_agent(self, user_id: Optional[str], session_id: Optional[str]) -> None:
        model = AzureOpenAI(self.azureOpenAiconfig.AZURE_OPENAI_LLM_DEPLOYMENT_NAME)

        self.agent = Agent(
            model=model,
            session_id=session_id,
            user_id=user_id,
            enable_agentic_memory=True,
            enable_user_memories=True,
            storage=get_storage_db(user_id=user_id),
            add_history_to_messages=True,
            description=(
                "You are an expert database assistant."
                "Your task is to provide clear and concise answers in natural language"
                "Use the toolkit function to get the information from the database."
            ),
            instructions=(
                "You will receive a user question."
                "You will obtain the sql response using the toolkit function."
                "Your response should be a one-sentence answer that addresses the user's question."
                "If the toolkit function fails because the user try to execute an insert, update or delete operation, say 'I can't insert, update or delete data into the database'."
                "If the toolkit function fails, say 'I can't respond to that question at this moment, try again later'."
                "If you cannot answer the question, say 'I don't have the information to answer that question'."
            ),
            tools=[self.sql_agent_toolkit],
        )

    async def run(
        self,
        user_question: str,
        user_id: Optional[str],
        session_id: Optional[str],
    ) -> str:
        try:
            self.logger.debug("Querying Agno agent for summarization")
            self.logger.debug("User question: %s", user_question)

            self._init_agent(user_id, session_id)

            response: RunResponse = await self.agent.arun(
                message=user_question, user_id=user_id
            )

            self.logger.debug("Generated summary from Agno: %s", response.content)
            return response.content
        except Exception as e:
            self.logger.exception(
                f"Failed to summarize answer with Agno for question: {user_question}.",
                e,
            )
            raise RuntimeError("Failed to summarize answer with Agno agent.") from e
