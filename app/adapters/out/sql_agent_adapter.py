import logging
from typing import Dict

from agno.agent import Agent
from agno.models.base import Model
from agno.run.response import RunResponse
from agno.tools.postgres import PostgresTools
from domain.ports.agent_port import AgentInterface


class SQLAgentAdapter(AgentInterface):
    def __init__(self, model: Model, postgres_toolkit: PostgresTools):
        self.agent = Agent(
            model=model,
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
        )

        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self, user_question: str, context: Dict) -> str:
        try:
            self.logger.debug("Querying Agno agent for sql generation")
            self.logger.debug("User question: %s", user_question)

            self.agent.context = context
            response: RunResponse = await self.agent.arun(user_question)

            self.logger.debug("Generated sql from Agno: %s", response.content)

            return response.content
        except Exception as e:
            self.logger.exception("Error querying Agno agent for sql generation: %s", e)
            raise e
