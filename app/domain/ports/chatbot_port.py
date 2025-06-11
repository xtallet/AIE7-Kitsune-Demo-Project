from abc import ABC, abstractmethod


class ChatbotInterface(ABC):
    """This is the Chatbot port interface.

    It defines the methods that the Chatbot adapter must implement.
    """

    @abstractmethod
    async def answer(self, question: str) -> str:
        pass
