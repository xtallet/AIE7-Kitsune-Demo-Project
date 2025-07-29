import time
from datetime import datetime, timezone

import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.mark.usefixtures("setup_and_teardown_mongo_db")
class TestChatAgentRepository:
    def test_get_last_session_empty(self):
        result = self.repo.get_last_session(self.test_user_id)

        assert result is None

    def test_create_session(self):
        test_data = {"message": "Hello world"}
        session_id = self.repo.create_session(self.test_user_id, test_data)

        assert session_id is not None

        collection = self.repo.db[self.test_user_id]
        doc = collection.find_one({"_id": session_id})
        assert doc is not None
        assert doc["message"] == "Hello world"
        assert doc["user_id"] == self.test_user_id
        assert "created_at" in doc

    def test_get_last_session(self):
        first_data = {
            "message": "First message",
            "created_at": int(datetime.now(timezone.utc).timestamp()),
        }
        self.repo.create_session(self.test_user_id, first_data)

        time.sleep(1)

        second_data = {
            "message": "Second message",
            "created_at": int(datetime.now(timezone.utc).timestamp()),
        }
        self.repo.create_session(self.test_user_id, second_data)

        last_session = self.repo.get_last_session(self.test_user_id)

        assert last_session is not None

    def test_create_or_get_last_session_existing(self):
        test_data = {
            "message": "Existing session",
            "created_at": int(datetime.now(timezone.utc).timestamp()),
        }
        created_id = self.repo.create_session(self.test_user_id, test_data)

        result = self.repo.create_or_get_last_session(self.test_user_id)

        assert result == created_id

    def test_create_or_get_last_session_new(self):
        result = self.repo.create_or_get_last_session(self.test_user_id)

        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 36
