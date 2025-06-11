from abc import ABC, abstractmethod


class GuardrailInterface(ABC):
    """This is the Guardrail port interface.

    It defines the methods that the Guardrail adapter must implement.
    """

    @abstractmethod
    async def validate_question(self, user_question: str) -> bool:
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Test the connectivity and functionality of the Guardrails service.

        Returns True if the service is operational, otherwise raises an exception.
        """
        pass
