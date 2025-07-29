import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

from fastapi import FastAPI
from pydantic import BaseModel, field_validator

from app.adapters.out.adapter_factory import (
    build_cache_adapter,
    build_guardrail_adapter,
    build_knowledge_base_adapter,
)
from app.agents.chat_agent import ChatbotAgent
from app.application.chatbot import KitsuneChatbot
from app.repositories.chat_agent_repository import ChatAgentRepository
from app.toolkits.postgres_toolkit import _get_postgres_tools


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
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    service_errors = []

    # Test Redis cache connectivity
    logger.info("Testing Redis cache connectivity...")
    cache_adapter = build_cache_adapter()
    if not await cache_adapter.ping():
        service_errors.append("Redis cache connectivity test failed.")

    # Testing lancedb
    logger.info("Testing LanceDB connectivity...")
    lancedb_adapter = await build_knowledge_base_adapter()
    if not await lancedb_adapter.ping():
        service_errors.append("Knowledge DB connection is not open.")

    # Test MongoDB connectivity
    logger.info("Testing MongoDB connectivity...")
    chat_agent_repo = ChatAgentRepository()
    if not await chat_agent_repo.ping():
        service_errors.append("MongoDB connectivity test failed.")

    logger.info("Testing Postgres connectivity...")
    tool = _get_postgres_tools()
    result = tool.run_query(
        "SELECT COUNT(cp.policy_reference) AS total_policies FROM get_premiums() cp;"
    )
    if not result:
        service_errors.append("Postgres connectivity test failed.")
    logger.info("Postgres connectivity test passed. Total policies: %s", result)

    if service_errors:
        logger.error("\n".join(service_errors))
        raise RuntimeError(f"Checks failed: {'; '.join(service_errors)}")
    else:
        yield


app = FastAPI(lifespan=lifespan)


class ChatbotService:
    def __init__(self):
        self.agent = None
        self._initialized = False
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger("fastapi")
        self.logger.setLevel(logging.INFO)

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


chatbot_service = ChatbotService()


@app.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    response, session_id = await chatbot_service.answer(
        request.question, request.user_id, request.session_id
    )
    return {"response": response, "session_id": session_id}
