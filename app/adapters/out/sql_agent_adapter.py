import logging
from agno.run.response import RunResponse
from agno.agent import Agent
from agno.models.base import Model
from domain.ports.agent_port import AgentInterface

class SQLAgentAdapter(AgentInterface):
    def __init__(self, model: Model):
        self.agent = Agent(
            model=model,
            description=(
                "You are a database expert assistant. Your task is to receive a natural language question"
                "use the context provided with the questions, their SQL queries, and their chain of thoughts (COT)"
                "and generate a precise SQL query to answer the user's question."
            ),
            instructions=(
                "You will receive a user question."
                "You will receive a context that contains, under the 'example' key, the questions, their SQL queries, and their chain of thoughts (COT)."
                "Your response should be a SQL query that addresses the user's question."
                "You must respond only with the SQL query in its pure form, without additional explanations."
            ),
            add_context=True,
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
      
    async def run(self, user_question: str, context: str):
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
    