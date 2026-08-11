import pytest
from httpx import ASGITransport, AsyncClient

from driftsentry_api.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_liveness_returns_service_metadata(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "service": "DriftSentry API",
        "version": "0.1.0",
        "environment": "development",
    }


@pytest.mark.asyncio
async def test_root_points_to_api_documentation(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["documentation"] == "/docs"
