from fastapi import APIRouter

from driftsentry_api.api.routes.events import router as events_router
from driftsentry_api.api.routes.health import router as health_router
from driftsentry_api.api.routes.models import router as models_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(events_router)
