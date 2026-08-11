from fastapi import APIRouter

from driftsentry_api.api.routes.health import router as health_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
