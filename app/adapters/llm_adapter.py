import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

from app.domain.domain import CbotState

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LLMAdapter:
    def __init__(
        self,
        model_name: str,
        azure_deployment: str,
        azure_endpoint: str,
        api_version: str,
    ) -> None:
        self.llm = AzureChatOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            temperature=0.3,
            max_tokens=2500,
        )
        self.model_name = model_name
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a database expert assistant. Your task is to receive a natural language question, "
                    "use the context provided with the questions, their SQL queries, and their chain of thoughts (COT)"
                    "and generate a precise SQL query to answer the user's question."
                    "You must respond only with the SQL query in its pure form, without additional explanations.",
                ),
                (
                    "user",
                    "Question: {question}\n\nContext:\n{context}",
                ),
            ]
        )

    async def generate_sql_query(self, state: CbotState) -> CbotState:
        """Generates a SQL query using Azure OpenAI (GPT-4o model), given a context (history of previous questions, CoT and SQL) and a new question from the user."""
        try:
            chain = self.prompt_template | self.llm
            response = chain.invoke(
                {
                    "question": state.question,
                    "context": state.context,
                }
            )

            state.sql_query = response.content
            logger.info("Generated SQL query: %s", state.sql_query)
            return state
        except Exception as e:
            logger.error(
                "Failed to generate SQL query for question: %s, Error: %s",
                state.question,
                str(e),
            )
            raise RuntimeError("Failed to generate SQL query.") from e

    async def ping(self) -> bool:
        """Test connectivity with the LLM by sending a simple request.

        Returns True if the LLM responds successfully, otherwise raises an exception.
        """
        try:
            response = await self.llm.invoke(
                [("system", "ping")],
            )
            logger.info("LLM service ping successful.")
            return response is not None
        except Exception as e:
            logger.exception("LLM connectivity test failed", exc_info=e)
            raise RuntimeError(f"LLM connectivity test failed: {str(e)}")
