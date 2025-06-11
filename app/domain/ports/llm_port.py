from abc import ABC, abstractmethod
from typing import Any


class LLM(ABC):
    @abstractmethod
    async def generate_sql_query(self, user_question: str, context: str) -> str:
        pass

    @abstractmethod
    async def summarize_answer(self, user_question: str, query_result: Any) -> str:
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Test connectivity with the LLM service.

        :return: True if the service is reachable, otherwise raise an exception.
        """
        pass
