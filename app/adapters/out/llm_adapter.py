import logging

from openai import AsyncAzureOpenAI

from app.domain.ports.llm_port import LLM


class LLMAdapter(LLM):
    def __init__(
        self,
        model_name: str,
        azure_deployment: str,
        azure_endpoint: str,
        api_version: str,
        api_key: str,
    ) -> None:
        self.client = AsyncAzureOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            api_key=api_key,
        )
        self.model_name = model_name
        self.logger = logging.getLogger(self.__class__.__name__)

    async def generate_sql_query(self, user_question: str, context: str) -> str:
        """Generates a SQL query using Azure OpenAI (GPT-4o model), given a context (history of previous questions, CoT and SQL) and a new question from the user."""
        system_prompt = (
            "You are a database expert assistant. Your task is to receive a natural language question, "
            "use the context provided with the questions, their SQL queries, and their chain of thoughts (COT)"
            "and generate a precise SQL query to answer the user's question."
            "You must respond only with the SQL query in its pure form, without additional explanations."
        )
        try:
            # self.logger.info("Generating SQL query for user question: %s", user_question)
            self.logger.debug("Context provided: %s", context)

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Question: {user_question}\n\nContext:\n{context}",
                    },
                ],
                temperature=0.3,
                max_tokens=2500,
            )

            sql_query = response.choices[0].message.content
            self.logger.debug("Generated SQL query: %s", sql_query)
            return sql_query
        except Exception as e:
            self.logger.error(
                "Failed to generate SQL query for question: %s, Error: %s",
                user_question,
                str(e),
            )
            raise RuntimeError("Failed to generate SQL query.") from e

    async def ping(self) -> bool:
        """Test connectivity with the LLM by sending a simple request.

        Returns True if the LLM responds successfully, otherwise raises an exception.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": "ping"}],
                temperature=0,
                max_tokens=1,
            )
            self.logger.info("LLM service ping successful.")
            return response is not None
        except Exception as e:
            self.logger.exception("LLM connectivity test failed", e)
            raise RuntimeError(f"LLM connectivity test failed: {str(e)}")
