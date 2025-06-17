import logging
from typing import Optional, Tuple

from app.adapters.out.agent_adapter import ChatbotAgentAdapter
from app.adapters.out.sql_agent_adapter import SQLAgentAdapter
from app.domain.ports.cache_port import Cache
from app.domain.ports.chatbot_port import ChatbotInterface
from app.domain.ports.guardrail_port import GuardrailInterface
from app.domain.ports.knowledge_base_port import KnowledgeBase


class KitsuneChatbot(ChatbotInterface):
    def __init__(
        self,
        cache: Cache,
        knowledge_base: KnowledgeBase,
        guardrail: GuardrailInterface,
        logger: logging.Logger,
        chatbot_agent: ChatbotAgentAdapter,
        sql_agent: SQLAgentAdapter,
    ) -> None:
        super().__init__()
        self.cache_service = cache
        self.knowledge_base_service = knowledge_base
        self.guardrail_service = guardrail
        self.logger = logger
        self.chatbot_agent = chatbot_agent
        self.sql_agent = sql_agent

    async def answer(self, question: str) -> str:
        self.logger.info(f"Question received: {question}")

        if await self.guardrail_service.validate_question(question):
            if cache_answer := await self._get_answer_cached(question):
                return cache_answer

            context, sql_answer = await self._get_and_execute_sql_from_model(question)
            nl_answer = await self._get_natural_language_answer(question, sql_answer)
            await self._cache_answer(question, context, sql_answer, nl_answer)
        else:
            self.logger.warning(f"Question not related to insurance topics: {question}")
            nl_answer = (
                "Sorry, I can only answer questions related to insurance policies."
            )

        return nl_answer

    async def _get_answer_cached(self, question: str) -> Optional[str]:
        cache_answer = await self.cache_service.get_from_cache(question)
        if cache_answer:
            self.logger.debug(f"⚡ Answer found in cache for question: {question}")
            return cache_answer["answer"]

        return None

    async def _get_and_execute_sql_from_model(self, question: str) -> Tuple[str, str]:
        context = await self.knowledge_base_service.search(query=question)
        sql_answer = await self.sql_agent.run(
            user_question=question, context={"example": context}
        )

        self.logger.debug(
            f"Question: {question}.\n SQL answer: {sql_answer}.\n Context: {context}"
        )

        return context, sql_answer

    async def _get_natural_language_answer(self, question: str, sql_answer: str) -> str:
        nl_answer = await self.chatbot_agent.run(
            user_question=question, context={"sql_answer": sql_answer}
        )
        self.logger.debug(f"Question: {question}.\n Summarized answer: {nl_answer}")

        return nl_answer

    async def _cache_answer(
        self, question: str, context: str, sql_query: str, nl_answer: str
    ) -> None:
        await self.cache_service.save_to_cache(
            question,
            {
                "question": question,
                "context": context,
                "sql_generated": sql_query,
                "answer": nl_answer,
            },
        )
