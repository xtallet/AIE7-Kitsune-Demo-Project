from abc import ABC, abstractmethod


class LLM(ABC):
    @abstractmethod
    async def generate_sql_query(self, user_question: str, context: str) -> str:
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Test connectivity with the LLM service.

        :return: True if the service is reachable, otherwise raise an exception.
        """
        pass
