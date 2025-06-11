from abc import ABC, abstractmethod
from typing import Any


class KitsuneDB(ABC):
    """This is the KitsuneDB port interface.

    It defines the methods that the KitsuneDB adapter must implement.
    """

    @abstractmethod
    async def run_sql_query(self, query: str) -> Any:
        """Run a SQL query on the KitsuneDB database.

        :param query: The SQL query to run.
        :return: The result of the query.
        """
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Test connectivity with the database by executing a simple query.

        Returns True if the query executes successfully, otherwise raises an exception.
        """
        pass
