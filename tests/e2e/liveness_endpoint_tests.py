import pytest


class TestLivenessEndpoint:
    """End-to-end tests for the liveness endpoint."""

    @pytest.mark.asyncio
    async def test_liveness_alive(self, test_client):
        response = test_client.get("/liveness")

        assert response.status_code == 200
        assert response.json() == {"status": "alive"}
