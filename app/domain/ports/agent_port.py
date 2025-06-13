from abc import ABC, abstractmethod
from typing import Dict


class AgentInterface(ABC):
    @abstractmethod
    async def run(self, user_question: str, context: Dict) -> str:
        pass
