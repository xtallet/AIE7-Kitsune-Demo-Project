import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Tuple

from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from ray import serve

from app.adapters.out.adapter_factory import (
    build_cache_adapter,
    build_guardrail_adapter,
    build_knowledge_base_adapter,
)
from app.agents.chat_agent import ChatbotAgent
from app.application.chatbot import KitsuneChatbot


class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str]
    question: str

    @field_validator("question")
    def validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be empty or whitespace")
        return value


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    logger = logging.getLogger("ray.serve")
    logger.setLevel(logging.INFO)
    service_errors = []

    # Test Redis cache connectivity
    cache_adapter = build_cache_adapter()
    if not await cache_adapter.ping():
        service_errors.append("Redis cache connectivity test failed.")

    # Testing lancedb
    lancedb_adapter = await build_knowledge_base_adapter()
    if not await lancedb_adapter.ping():
        service_errors.append("Knowledge DB connection is not open.")

    # Test Guardrails connectivity
    guardrail_adapter = build_guardrail_adapter()
    if not await guardrail_adapter.ping():
        service_errors.append("Guardrails service connectivity test failed.")

    if service_errors:
        logger.error("\n".join(service_errors))
    else:
        yield


fastapi_app = FastAPI(lifespan=lifespan)


@serve.deployment
class ChatbotService:
    def __init__(self):
        self.agent = None
        self._initialized = False
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger("ray.serve")

    async def _async_init(self):
        if not self._initialized:
            async with self._lock:
                if not self._initialized:  # Double-check inside the lock
                    self.logger.info("Initializing the chatbot agent...")
                    self.agent = KitsuneChatbot(
                        cache=build_cache_adapter(),
                        guardrail=build_guardrail_adapter(),
                        logger=self.logger,
                        chatbot_agent=ChatbotAgent(),
                    )
                    self._initialized = True
                    self.logger.info("Chatbot agent initialized successfully.")

    async def answer(
        self, question: str, user_id: str, session_id: Optional[str] = None
    ) -> Tuple[str, str]:
        await self._async_init()
        return await self.agent.answer(question, user_id, session_id)


@serve.deployment
@serve.ingress(fastapi_app)
class ChatbotAPIIngress:
    def __init__(self, chatbot_handle):
        self.chatbot_handle = chatbot_handle

    @fastapi_app.post("/chat")
    async def chat(self, request: ChatRequest):
        response, session_id = await self.chatbot_handle.answer.remote(
            request.question, request.user_id, request.session_id
        )
        return {"answer": response, "session_id": session_id}


entrypoint = ChatbotAPIIngress.bind(ChatbotService.bind())  # type: ignore[attr-defined]
