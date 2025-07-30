import time

import pytest
from fastapi.testclient import TestClient
from repositories.chat_agent_repository import ChatAgentRepository


@pytest.fixture()
def setup_and_teardown_mongo_db(request):
    request.cls.repo = ChatAgentRepository()
    request.cls.test_user_id = f"test_user_{int(time.time())}"

    yield

    db_name = request.cls.repo.db.name
    request.cls.repo.client.drop_database(db_name)


@pytest.fixture
def test_client():
    from app.main import app

    return TestClient(app)
