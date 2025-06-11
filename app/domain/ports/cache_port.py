from abc import ABC, abstractmethod
from typing import Any


class Cache(ABC):
    @abstractmethod
    async def save_to_cache(self, key: str, data: Any) -> None:
        pass

    @abstractmethod
    async def get_from_cache(self, key: str) -> Any:
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Test connectivity with the cache service.

        :return: True if the service is reachable, otherwise raise an exception.
        """
        pass
