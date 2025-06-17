import asyncio
import logging

from dotenv import load_dotenv

from app.adapters.out.adapter_factory import (
    build_agent,
    build_cache_adapter,
    build_guardrail_adapter,
    build_knowledge_base_adapter,
    build_sql_agent,
)
from app.application.chatbot import KitsuneChatbot

env_vars = load_dotenv()


async def main():
    lancedb_adapter = await build_knowledge_base_adapter()
    chatbot_agent = build_agent()
    sql_agent = await build_sql_agent()
    agent = KitsuneChatbot(
        cache=build_cache_adapter(),
        knowledge_base=lancedb_adapter,
        guardrail=build_guardrail_adapter(),
        logger=logging.getLogger("KitsuneChatbot"),
        sql_agent=sql_agent,
        chatbot_agent=chatbot_agent,
    )
    while True:
        question = input("User: ")
        if question.lower() in ["quit", "exit"]:
            break

        print(f"{await agent.answer(question)}")


if __name__ == "__main__":
    asyncio.run(main())
