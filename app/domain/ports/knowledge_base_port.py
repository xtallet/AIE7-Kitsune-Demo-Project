from abc import ABC, abstractmethod


class KnowledgeBase(ABC):

    @abstractmethod
    async def create_embedding(self, text: str) -> list[float]:
        """Generates an embedding for the provided text using the specified OpenAI model.

        :param text: Text to be processed.
        :return: List of float values representing the embedding.
        """
        pass

    @abstractmethod
    async def search(self, query: str, k: int = 8) -> str:
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Test connectivity with the knowledge base.

        :return: True if the service is reachable, otherwise raise an exception.
        """
        pass
