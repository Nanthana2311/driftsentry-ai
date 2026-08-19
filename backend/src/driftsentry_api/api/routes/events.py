from fastapi import APIRouter, HTTPException, Query, status

from driftsentry_api.api.dependencies import AuthenticatedModel, DatabaseSession
from driftsentry_api.schemas.events import (
    EventBatchCreate,
    EventBatchResponse,
    EventListResponse,
    PredictionEventResponse,
)
from driftsentry_api.services.event_ingestion import (
    EventIngestionService,
    FeatureSchemaValidationError,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "/batch",
    response_model=EventBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_event_batch(
    payload: EventBatchCreate,
    model: AuthenticatedModel,
    session: DatabaseSession,
) -> EventBatchResponse:
    service = EventIngestionService(session)
    try:
        accepted, duplicates = await service.ingest(model, payload)
    except FeatureSchemaValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "feature_schema_invalid",
                "message": str(error),
                "errors": error.errors,
            },
        ) from error

    return EventBatchResponse(
        model_id=model.id,
        total=len(payload.events),
        accepted=accepted,
        duplicates=duplicates,
    )


@router.get("", response_model=EventListResponse)
async def list_events(
    model: AuthenticatedModel,
    session: DatabaseSession,
    limit: int = Query(default=50, ge=1, le=100),
) -> EventListResponse:
    events = await EventIngestionService(session).list_for_model(model.id, limit)
    items = [PredictionEventResponse.model_validate(event) for event in events]
    return EventListResponse(items=items, total=len(items))
