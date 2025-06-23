import logging
from typing import Dict, Callable

from agno.agent import Agent
from agno.models.base import Model
from agno.run.response import RunResponse

from app.agents.agent_port import AgentInterface
from agno.models.azure import AzureOpenAI
from app.config.settings import AzureOpenAIConfig
from app.toolkits.sql_agent_toolkit import sql_agent_toolkit

class ChatbotAgent(AgentInterface):
    def __init__(self) -> None:
        config = AzureOpenAIConfig()
        
        self.agent = Agent(
            model=AzureOpenAI(config.AZURE_OPENAI_LLM_DEPLOYMENT_NAME),
            description=(
                "You are an expert database assistant."
                "Your task is to provide clear and concise answers in natural language"
                "Use the toolkit function to get the information from the database."
                #"based on the results of SQL queries."
            ),
            instructions=(
                "You will receive a user question."
                "You will obtain the sql response using the toolkit function."
                "Your response should be a one-sentence answer that addresses the user's question."
            ),
            tools=[sql_agent_toolkit],
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self, user_question: str) -> str:
        try:
            self.logger.debug("Querying Agno agent for summarization")
            self.logger.debug("User question: %s", user_question)

            response: RunResponse = await self.agent.arun(user_question)

            self.logger.debug("Generated summary from Agno: %s", response.content)
            return response.content

        except Exception as e:
            self.logger.exception(
                f"Failed to summarize answer with Agno for question: {user_question}.",
                e,
            )
            raise RuntimeError("Failed to summarize answer with Agno agent.") from e
