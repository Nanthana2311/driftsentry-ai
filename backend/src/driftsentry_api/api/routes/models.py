from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from driftsentry_api.api.dependencies import DatabaseSession
from driftsentry_api.schemas.models import (
    ModelCreate,
    ModelListResponse,
    ModelRegistrationResponse,
    ModelResponse,
)
from driftsentry_api.services.model_registry import (
    ModelAlreadyExistsError,
    ModelNotFoundError,
    ModelRegistryService,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.post(
    "",
    response_model=ModelRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_model(
    payload: ModelCreate, session: DatabaseSession
) -> ModelRegistrationResponse:
    service = ModelRegistryService(session)
    try:
        model, raw_key = await service.create(payload)
    except ModelAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "model_version_exists",
                "message": f"Model '{payload.name}' version '{payload.version}' already exists.",
            },
        ) from error

    response = ModelResponse.model_validate(model)
    return ModelRegistrationResponse(**response.model_dump(), ingestion_key=raw_key)


@router.get("", response_model=ModelListResponse)
async def list_models(session: DatabaseSession) -> ModelListResponse:
    models = await ModelRegistryService(session).list()
    items = [ModelResponse.model_validate(model) for model in models]
    return ModelListResponse(items=items, total=len(items))


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: UUID, session: DatabaseSession) -> ModelResponse:
    try:
        model = await ModelRegistryService(session).get(model_id)
    except ModelNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "model_not_found", "message": "Model was not found."},
        ) from error
    return ModelResponse.model_validate(model)
