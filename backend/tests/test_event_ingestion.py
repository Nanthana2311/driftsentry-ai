from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from driftsentry_api.api.dependencies import get_db_session
from driftsentry_api.db.base import Base
from driftsentry_api.db.models import PredictionEvent
from driftsentry_api.main import app

MODEL_PAYLOAD: dict[str, Any] = {
    "name": "customer-churn",
    "version": "1.0.1",
    "task_type": "binary_classification",
    "features": [
        {
            "name": "tenure",
            "data_type": "numerical",
            "nullable": False,
            "constraints": {"min": 0},
        },
        {
            "name": "MonthlyCharges",
            "data_type": "numerical",
            "nullable": False,
            "constraints": {"min": 0},
        },
        {
            "name": "Contract",
            "data_type": "categorical",
            "nullable": False,
            "constraints": {"allowed": ["Month-to-month", "One year", "Two year"]},
        },
    ],
}
EVENT_BATCH: dict[str, Any] = {
    "events": [
        {
            "event_id": "prediction-1001",
            "occurred_at": "2026-08-18T08:00:00Z",
            "features": {
                "tenure": 4,
                "MonthlyCharges": 89.5,
                "Contract": "Month-to-month",
            },
            "prediction": 1,
            "probability": 0.82,
        },
        {
            "event_id": "prediction-1002",
            "occurred_at": "2026-08-18T08:01:00Z",
            "features": {
                "tenure": 48,
                "MonthlyCharges": 45.0,
                "Contract": "Two year",
            },
            "prediction": 0,
            "probability": 0.12,
        },
    ]
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


async def _register_model(client: AsyncClient) -> str:
    response = await client.post("/api/v1/models", json=MODEL_PAYLOAD)
    assert response.status_code == 201
    return str(response.json()["ingestion_key"])


@pytest.mark.asyncio
async def test_valid_batch_is_ingested_and_listed(client: AsyncClient) -> None:
    key = await _register_model(client)
    headers = {"X-DriftSentry-Key": key}

    ingested = await client.post("/api/v1/events/batch", json=EVENT_BATCH, headers=headers)
    listed = await client.get("/api/v1/events", headers=headers)

    assert ingested.status_code == 202
    assert ingested.json()["accepted"] == 2
    assert ingested.json()["duplicates"] == 0
    assert listed.status_code == 200
    assert listed.json()["total"] == 2
    assert {item["event_id"] for item in listed.json()["items"]} == {
        "prediction-1001",
        "prediction-1002",
    }


@pytest.mark.asyncio
async def test_retry_is_idempotent(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    key = await _register_model(client)
    headers = {"X-DriftSentry-Key": key}

    first = await client.post("/api/v1/events/batch", json=EVENT_BATCH, headers=headers)
    retry = await client.post("/api/v1/events/batch", json=EVENT_BATCH, headers=headers)

    assert first.json()["accepted"] == 2
    assert retry.status_code == 202
    assert retry.json()["accepted"] == 0
    assert retry.json()["duplicates"] == 2
    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(PredictionEvent))
    assert count == 2


@pytest.mark.asyncio
async def test_missing_and_invalid_keys_return_unauthorized(client: AsyncClient) -> None:
    missing = await client.post("/api/v1/events/batch", json=EVENT_BATCH)
    invalid = await client.post(
        "/api/v1/events/batch",
        json=EVENT_BATCH,
        headers={"X-DriftSentry-Key": "ds_live_not-a-real-secret-key"},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert missing.headers["www-authenticate"] == "ApiKey"


@pytest.mark.asyncio
async def test_feature_schema_mismatch_returns_validation_details(client: AsyncClient) -> None:
    key = await _register_model(client)
    invalid_batch = {
        "events": [
            {
                **EVENT_BATCH["events"][0],
                "features": {"tenure": -1, "UnexpectedFeature": "value"},
            }
        ]
    }

    response = await client.post(
        "/api/v1/events/batch",
        json=invalid_batch,
        headers={"X-DriftSentry-Key": key},
    )

    assert response.status_code == 422
    errors = response.json()["detail"]["errors"]
    assert {error["code"] for error in errors} == {
        "below_minimum",
        "missing_feature",
        "unknown_feature",
    }


@pytest.mark.asyncio
async def test_duplicate_ids_inside_one_batch_are_rejected(client: AsyncClient) -> None:
    key = await _register_model(client)
    duplicate_batch = {"events": [EVENT_BATCH["events"][0], EVENT_BATCH["events"][0]]}

    response = await client.post(
        "/api/v1/events/batch",
        json=duplicate_batch,
        headers={"X-DriftSentry-Key": key},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_probability_and_timestamp_are_validated(client: AsyncClient) -> None:
    key = await _register_model(client)
    invalid_event = {
        **EVENT_BATCH["events"][0],
        "occurred_at": "2026-08-18T08:00:00",
        "probability": 1.5,
    }

    response = await client.post(
        "/api/v1/events/batch",
        json={"events": [invalid_event]},
        headers={"X-DriftSentry-Key": key},
    )

    assert response.status_code == 422
