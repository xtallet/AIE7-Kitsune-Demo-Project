import logging
from typing import Dict, Optional, Tuple

from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.run.response import RunResponse
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from app.agents.storage import get_storage_db
from app.config.settings import AzureOpenAIConfig, LangSmithConfig

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ChatbotAgent:
    def __init__(self) -> None:
        self.azure_open_ai_config = AzureOpenAIConfig()
        self._langsmith_config = LangSmithConfig()

    def _init_agent(
        self,
        context: Dict,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        model = AzureOpenAI(self.azure_open_ai_config.AZURE_OPENAI_LLM_DEPLOYMENT_NAME)

        # Configure the Langsmith trace provider
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(
            SimpleSpanProcessor(
                OTLPSpanExporter(
                    endpoint="https://eu.api.smith.langchain.com/otel/v1/traces",
                    headers={
                        "x-api-key": self._langsmith_config.LANGSMITH_API_KEY,
                        "Langsmith-Project": self._langsmith_config.LANGSMITH_PROJECT,
                    },
                )
            )
        )
        trace_api.set_tracer_provider(tracer_provider=tracer_provider)

        AgnoInstrumentor().instrument()

        self.agent = Agent(
            model=model,
            context=context,
            add_context=True,
            session_id=session_id,
            user_id=user_id,
            enable_agentic_memory=True,
            enable_user_memories=True,
            storage=get_storage_db(user_id=user_id) if user_id is not None else None,
            add_history_to_messages=True,
            description=(
                "You are an expert insurance events MongoDB interpreter."
                "Your task is to provide clear and concise answers in natural language"
            ),
            instructions=(
                "You will receive a user question."
                "You will receive MongoDB insurance events context as context."
                "Your response should be a one-sentence answer that addresses the user's question."
                "Use only the context to answer the question."
                "You can not perform any actions or execute any code, just provide a summary based on the context."
                "If an action is required, you should say 'I can't perform any action'."
                "If you cannot answer the question, say 'I don't have the information to answer that question'."
            ),
        )

        # old version
        #     description=(
        #         "You are an expert sql result interpreter."
        #         "Your task is to provide clear and concise answers in natural language"
        #     ),
        #     instructions=(
        #         "You will receive a user question."
        #         "You will receive the sql result as context"
        #         "Your response should be a one-sentence answer that addresses the user's question."
        #         "Use only the context to answer the question."
        #         "You can not perform any actions or execute any code, just provide a summary based on the context."
        #         "If an action is required, you should say 'I can't perform any action'."
        #         "If you cannot answer the question, say 'I don't have the information to answer that question'."
        #     ),
        # )

    async def run(
        self,
        user_question: str,
        context: Dict,
        user_id: Optional[str],
        session_id: Optional[str],
    ) -> Tuple[str, str]:
        try:
            print(f'context from chat_agent: {context}')
            logger.info("Querying Agno agent for summarization")
            logger.info("User question: %s", user_question)

            self._init_agent(context, user_id, session_id)

            response: RunResponse = await self.agent.arun(
                message=user_question, user_id=user_id
            )

            logger.info("Generated summary from Agno: %s", response.content)
            return response.content, self.agent.session_id
        except Exception as e:
            logger.exception(
                f"Failed to summarize answer with Agno for question: {user_question}.",
                exc_info=e,
            )
            raise RuntimeError("Failed to summarize answer with Agno agent.") from e
