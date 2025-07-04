import logging
from typing import Dict, Optional

from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.run.response import RunResponse

from app.agents.agent_port import AgentInterface
from app.config.settings import (
    AzureOpenAIConfig,
)
from app.toolkits.postgres_toolkit import postgres_toolkit


class SQLAgent(AgentInterface):
    def __init__(self, context: Dict) -> None:
        config = AzureOpenAIConfig()

        self.agent = Agent(
            model=AzureOpenAI(config.AZURE_OPENAI_LLM_DEPLOYMENT_NAME),
            description=(
                "You are a database assistant. "
                "Given a user question and a context with example questions, their SQL queries, and reasoning steps, "
                "your task is to build and run a SQL query from the given context to answer the user's question, "
                "execute the query using the 'run_query' function with the sql query as 'query' parameter, and return only the result of the executed query with no extra explanation"
            ),
            instructions=(
                "You will receive a user question and a context under the 'example' key containing previous questions, their SQL queries, and reasoning (COT)"
                "use this context to select the most relevant SQL query"
                "use 'run_query' function to execute the query passing the sql query as 'query' parameter"
                "return only the result of the executed query with no extra explanation"
            ),
            add_context=True,
            tools=[postgres_toolkit],
            context=context,
        )

        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(
        self,
        user_question: str,
        user_id: Optional[str],
        session_id: Optional[str],
    ) -> str:
        try:
            self.logger.debug("Querying Agno agent for sql generation")
            self.logger.debug("User question: %s", user_question)

            response: RunResponse = await self.agent.arun(user_question)

            self.logger.debug("Generated sql from Agno: %s", response.content)

            return response.content
        except Exception as e:
            self.logger.exception("Error querying Agno agent for sql generation: %s", e)
            raise e
