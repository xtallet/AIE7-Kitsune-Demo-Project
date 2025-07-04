from abc import ABC, abstractmethod
from typing import Optional, Tuple


class ChatbotInterface(ABC):
    """This is the Chatbot port interface.

    It defines the methods that the Chatbot adapter must implement.
    """

    @abstractmethod
    async def answer(
        self, question: str, user_id: str, session_id: Optional[str] = None
    ) -> Tuple[str, str]:
        pass
