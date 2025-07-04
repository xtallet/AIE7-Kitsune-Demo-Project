from abc import ABC, abstractmethod
from typing import Optional


class AgentInterface(ABC):
    @abstractmethod
    async def run(
        self,
        user_question: str,
        user_id: Optional[str],
        session_id: Optional[str],
    ) -> str:
        pass
