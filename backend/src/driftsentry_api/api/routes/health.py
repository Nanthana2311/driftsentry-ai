from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text

from driftsentry_api.core.config import get_settings
from driftsentry_api.db.session import engine

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


class LivenessResponse(BaseModel):
    status: Literal["alive"]
    service: str
    version: str
    environment: str


@router.get("/live", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    """Confirm that the API process is alive without checking dependencies."""

    return LivenessResponse(
        status="alive",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready")
async def readiness() -> JSONResponse:
    """Check whether PostgreSQL and Redis are reachable."""

    checks: dict[str, str] = {}

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["postgres"] = "up"
    except Exception:  # Dependency details belong in server logs, not the public response.
        checks["postgres"] = "down"

    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis_client.ping()
        checks["redis"] = "up"
    except Exception:
        checks["redis"] = "down"
    finally:
        await redis_client.aclose()

    is_ready = all(value == "up" for value in checks.values())
    content: dict[str, object] = {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks,
    }
    return JSONResponse(status_code=200 if is_ready else 503, content=content)
