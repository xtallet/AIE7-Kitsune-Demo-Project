from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestReadinessEndpoint:
    """End-to-end tests for the readiness endpoint."""

    @pytest.mark.asyncio
    async def test_readiness_all_services_healthy(self, test_client):
        response = test_client.get("/readiness")

        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

    @pytest.mark.asyncio
    async def test_readiness_redis_failure(self, test_client):
        with patch("app.main.build_cache_adapter") as mock_cache:
            mock_cache.return_value.ping = AsyncMock(return_value=False)

            response = test_client.get("/readiness")
            assert response.status_code == 503
            assert (
                "Redis cache connectivity test failed."
                in response.json()["detail"]["errors"]
            )

    @pytest.mark.asyncio
    async def test_readiness_mongodb_failure(self, test_client):
        with patch("app.main.ChatAgentRepository") as mock_repo:
            mock_repo.return_value.ping = AsyncMock(return_value=False)

            response = test_client.get("/readiness")
            assert response.status_code == 503
            assert (
                "MongoDB connectivity test failed."
                in response.json()["detail"]["errors"]
            )

    @pytest.mark.asyncio
    async def test_readiness_postgres_failure(self, test_client):
        with patch("app.main._get_postgres_tools") as mock_postgres:
            mock_postgres.return_value.run_query = MagicMock(return_value=None)

            response = test_client.get("/readiness")
            assert response.status_code == 503
            assert (
                "Postgres connectivity test failed."
                in response.json()["detail"]["errors"]
            )

    @pytest.mark.asyncio
    async def test_readiness_lancedb_failure(self, test_client):
        with patch("app.main.build_knowledge_base_adapter") as mock_lance:
            mock_adapter = AsyncMock()
            mock_adapter.ping = AsyncMock(return_value=False)

            async def mock_build():
                return mock_adapter

            mock_lance.side_effect = mock_build

            response = test_client.get("/readiness")
            assert response.status_code == 503
            assert (
                "Knowledge DB connection is not open."
                in response.json()["detail"]["errors"]
            )
