import logging
from typing import Optional, Tuple

from app.agents.chat_agent import ChatbotAgent
from app.domain.ports.cache_port import Cache
from app.domain.ports.chatbot_port import ChatbotInterface
from app.domain.ports.guardrail_port import GuardrailInterface
from app.repositories.chat_agent_repository import ChatAgentRepository


class KitsuneChatbot(ChatbotInterface):
    def __init__(
        self,
        cache: Cache,
        guardrail: GuardrailInterface,
        logger: logging.Logger,
        chatbot_agent: ChatbotAgent,
    ) -> None:
        super().__init__()
        self.cache_service = cache
        self.guardrail_service = guardrail
        self.logger = logger
        self.chatbot_agent = chatbot_agent
        self.chat_agent_repository = ChatAgentRepository()

    async def answer(
        self, question: str, user_id: str, session_id: Optional[str] = None
    ) -> Tuple[str, str]:
        self.logger.info(f"Question received: {question}")

        if session_id is None:
            session_id = self.chat_agent_repository.create_or_get_last_session(
                user_id=user_id
            )

        if await self.guardrail_service.validate_question(question):
            if cache_answer := await self._get_answer_cached(question):
                return cache_answer, session_id

            nl_answer = await self.chatbot_agent.run(
                user_question=question, user_id=user_id, session_id=session_id
            )
            self.logger.debug(f"Question: {question}.\n Summarized answer: {nl_answer}")
            await self._cache_answer(question, nl_answer)
        else:
            self.logger.warning(f"Question not related to insurance topics: {question}")
            nl_answer = (
                "Sorry, I can only answer questions related to insurance policies."
            )

        return nl_answer, session_id

    async def _get_answer_cached(self, question: str) -> Optional[str]:
        cache_answer = await self.cache_service.get_from_cache(question)
        if cache_answer:
            self.logger.debug(f"⚡ Answer found in cache for question: {question}")
            return cache_answer["answer"]

        return None

    async def _cache_answer(self, question: str, nl_answer: str) -> None:
        await self.cache_service.save_to_cache(
            question,
            {
                "question": question,
                "answer": nl_answer,
            },
        )
