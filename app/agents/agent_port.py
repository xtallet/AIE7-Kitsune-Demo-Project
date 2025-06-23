from abc import ABC, abstractmethod


class AgentInterface(ABC):
    @abstractmethod
    async def run(self, user_question: str) -> str:
        pass
