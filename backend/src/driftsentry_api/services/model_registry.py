from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from driftsentry_api.core.config import get_settings
from driftsentry_api.core.security import generate_ingestion_key
from driftsentry_api.db.models import FeatureDefinition, RegisteredModel
from driftsentry_api.domain.enums import ModelStatus
from driftsentry_api.schemas.models import ModelCreate


class ModelAlreadyExistsError(Exception):
    """Raised when model name and version are already registered."""


class ModelNotFoundError(Exception):
    """Raised when a model ID does not exist."""


class ModelRegistryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    async def create(self, payload: ModelCreate) -> tuple[RegisteredModel, str]:
        raw_key, key_prefix, key_digest = generate_ingestion_key(
            self.settings.ingestion_key_pepper.get_secret_value()
        )
        model = RegisteredModel(
            name=payload.name,
            version=payload.version,
            task_type=payload.task_type,
            status=ModelStatus.ACTIVE,
            ingestion_key_prefix=key_prefix,
            ingestion_key_hash=key_digest,
            monitoring_config={},
            features=[
                FeatureDefinition(
                    name=feature.name,
                    data_type=feature.data_type,
                    nullable=feature.nullable,
                    constraints=feature.constraints,
                    position=position,
                )
                for position, feature in enumerate(payload.features)
            ],
        )
        self.session.add(model)

        try:
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            raise ModelAlreadyExistsError from error

        return model, raw_key

    async def list(self) -> list[RegisteredModel]:
        statement = (
            select(RegisteredModel)
            .options(selectinload(RegisteredModel.features))
            .order_by(RegisteredModel.created_at.desc())
        )
        result = await self.session.scalars(statement)
        return list(result.unique().all())

    async def get(self, model_id: UUID) -> RegisteredModel:
        statement = (
            select(RegisteredModel)
            .where(RegisteredModel.id == model_id)
            .options(selectinload(RegisteredModel.features))
        )
        model = await self.session.scalar(statement)
        if model is None:
            raise ModelNotFoundError
        return model
