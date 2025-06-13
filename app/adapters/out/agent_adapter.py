import logging
from typing import Dict

from agno.agent import Agent
from agno.models.base import Model
from agno.run.response import RunResponse
from domain.ports.agent_port import AgentInterface


class ChatbotAgentAdapter(AgentInterface):
    def __init__(self, model: Model) -> None:
        self.agent = Agent(
            model=model,
            description=(
                "You are an expert database assistant."
                "Your task is to provide clear and concise answers in natural language"
                "based on the results of SQL queries."
            ),
            instructions=(
                "You will receive a user question."
                "Your context will contain the result of a SQL query with the key sql_answer."
                "Your response should be a one-sentence answer that addresses the user's question."
            ),
            add_context=True,
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self, user_question: str, context: Dict) -> str:
        try:
            self.logger.debug("Querying Agno agent for summarization")
            self.logger.debug("User question: %s", user_question)

            self.agent.context = context
            response: RunResponse = await self.agent.arun(user_question)

            self.logger.debug("Generated summary from Agno: %s", response.content)
            return response.content

        except Exception as e:
            self.logger.error(
                "Failed to summarize answer with Agno for question: %s, Error: %s",
                user_question,
                str(e),
            )
            raise RuntimeError("Failed to summarize answer with Agno agent.") from e
