import asyncio
import logging

from dotenv import load_dotenv

from app.adapters.out.adapter_factory import (
    build_cache_adapter,
    build_guardrail_adapter,
    build_kitsune_db_adapter,
    build_knowledge_base_adapter,
    build_llm_adapter,
)
from app.application.chatbot import KitsuneChatbot

env_vars = load_dotenv()


async def main():
    lancedb_adapter = await build_knowledge_base_adapter()
    agent = KitsuneChatbot(
        cache=build_cache_adapter(),
        knowledge_base=lancedb_adapter,
        kitsune_db=build_kitsune_db_adapter(),
        llm=build_llm_adapter(),
        guardrail=build_guardrail_adapter(),
        logger=logging.getLogger("KitsuneChatbot"),
    )
    while True:
        question = input("User: ")
        if question.lower() in ["quit", "exit"]:
            break

        print(f"{await agent.answer(question)}")


if __name__ == "__main__":
    asyncio.run(main())
