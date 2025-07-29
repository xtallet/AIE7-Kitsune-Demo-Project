from abc import ABC, abstractmethod


class GuardrailInterface(ABC):
    """This is the Guardrail port interface.

    It defines the methods that the Guardrail adapter must implement.
    """

    @abstractmethod
    async def validate_question(self, user_question: str) -> bool:
        pass
