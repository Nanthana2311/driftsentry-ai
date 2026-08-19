from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from driftsentry_api.core.config import get_settings
from driftsentry_api.core.security import VISIBLE_PREFIX_LENGTH, verify_ingestion_key
from driftsentry_api.db.models import RegisteredModel
from driftsentry_api.domain.enums import ModelStatus


class InvalidIngestionKeyError(Exception):
    """Raised when an ingestion key cannot authenticate a model."""


class ModelInactiveError(Exception):
    """Raised when an authenticated model is not active."""


async def authenticate_ingestion_key(
    session: AsyncSession,
    raw_key: str,
) -> RegisteredModel:
    if len(raw_key) <= VISIBLE_PREFIX_LENGTH:
        raise InvalidIngestionKeyError

    prefix = raw_key[:VISIBLE_PREFIX_LENGTH]
    statement = (
        select(RegisteredModel)
        .where(RegisteredModel.ingestion_key_prefix == prefix)
        .options(selectinload(RegisteredModel.features))
    )
    candidates = list((await session.scalars(statement)).all())
    pepper = get_settings().ingestion_key_pepper.get_secret_value()

    model = next(
        (
            candidate
            for candidate in candidates
            if verify_ingestion_key(raw_key, candidate.ingestion_key_hash, pepper)
        ),
        None,
    )
    if model is None:
        raise InvalidIngestionKeyError
    if model.status is not ModelStatus.ACTIVE:
        raise ModelInactiveError
    return model
