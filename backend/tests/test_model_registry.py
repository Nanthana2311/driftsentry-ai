from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from driftsentry_api.api.dependencies import get_db_session
from driftsentry_api.core.security import hash_ingestion_key
from driftsentry_api.db.base import Base
from driftsentry_api.db.models import RegisteredModel
from driftsentry_api.main import app

MODEL_PAYLOAD: dict[str, Any] = {
    "name": "customer-churn",
    "version": "1.0.0",
    "task_type": "binary_classification",
    "features": [
        {"name": "tenure", "data_type": "numerical", "nullable": False},
        {"name": "MonthlyCharges", "data_type": "numerical", "nullable": False},
        {"name": "Contract", "data_type": "categorical", "nullable": False},
    ],
}


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_model_returns_key_once_and_persists_hash(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    response = await client.post("/api/v1/models", json=MODEL_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "customer-churn"
    assert body["status"] == "active"
    assert [feature["name"] for feature in body["features"]] == [
        "tenure",
        "MonthlyCharges",
        "Contract",
    ]
    raw_key = body["ingestion_key"]
    assert raw_key.startswith("ds_live_")

    async with session_factory() as session:
        model = await session.scalar(select(RegisteredModel))

    assert model is not None
    assert model.ingestion_key_hash != raw_key
    assert model.ingestion_key_hash == hash_ingestion_key(raw_key, "development-only-change-me")


@pytest.mark.asyncio
async def test_duplicate_model_version_returns_conflict(client: AsyncClient) -> None:
    first = await client.post("/api/v1/models", json=MODEL_PAYLOAD)
    duplicate = await client.post("/api/v1/models", json=MODEL_PAYLOAD)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "model_version_exists"


@pytest.mark.asyncio
async def test_list_and_get_do_not_expose_raw_or_hashed_key(client: AsyncClient) -> None:
    created = (await client.post("/api/v1/models", json=MODEL_PAYLOAD)).json()

    listed = await client.get("/api/v1/models")
    fetched = await client.get(f"/api/v1/models/{created['id']}")

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert "ingestion_key" not in listed.json()["items"][0]
    assert "ingestion_key_hash" not in listed.json()["items"][0]
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]
    assert "ingestion_key" not in fetched.json()
    assert "ingestion_key_hash" not in fetched.json()


@pytest.mark.asyncio
async def test_duplicate_feature_names_are_rejected(client: AsyncClient) -> None:
    payload = {
        **MODEL_PAYLOAD,
        "features": [
            {"name": "tenure", "data_type": "numerical"},
            {"name": "TENURE", "data_type": "numerical"},
        ],
    }

    response = await client.post("/api/v1/models", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unknown_model_returns_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/models/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "model_not_found"
