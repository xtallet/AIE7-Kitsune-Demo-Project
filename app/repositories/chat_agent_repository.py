import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

from dotenv import load_dotenv
from pymongo import DESCENDING, MongoClient

from app.config.settings import MongoDBConfig

load_dotenv()


class ChatAgentRepository:
    def __init__(self) -> None:
        config = MongoDBConfig()
        self.client = MongoClient(config.connection_string)
        self.db = self.client.chat_storage_db
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_or_get_last_session(self, user_id: str) -> str:
        return self.get_last_session_id(user_id=user_id) or str(uuid.uuid4())

    def get_last_session_id(self, user_id: str) -> str | None:
        session = self.get_last_session(user_id=user_id)

        if session and session.get("_id"):
            return str(session["_id"])

        return None

    def get_last_session(self, user_id: str) -> dict | None:
        collection = self.db[user_id]
        result = collection.find_one(filter={}, sort=[("created_at", DESCENDING)])

        return result

    def create_session(self, user_id: str, data: Optional[Dict] = None) -> str:
        session_data = data or {}

        if "user_id" not in session_data:
            session_data["user_id"] = user_id

        if "created_at" not in session_data:
            session_data["created_at"] = int(datetime.now(timezone.utc).timestamp())

        if "_id" not in session_data:
            session_data["_id"] = str(uuid.uuid4())

        collection = self.db[user_id]
        result = collection.insert_one(session_data)

        return str(result.inserted_id)

    async def ping(self) -> bool:
        try:
            # The ping command checks the connection to the MongoDB server
            self.client.admin.command("ping")
            return True
        except Exception as e:
            self.logger.exception("MongoDB connectivity test failed", exc_info=e)
            raise RuntimeError(f"MongoDB connectivity test failed: {str(e)}")

    def __enter__(self) -> "ChatAgentRepository":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        self.close()

    def close(self):
        if self.client:
            self.client.close()
