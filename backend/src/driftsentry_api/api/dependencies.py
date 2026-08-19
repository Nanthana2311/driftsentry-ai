from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from driftsentry_api.db.models import RegisteredModel
from driftsentry_api.db.session import async_session_factory
from driftsentry_api.services.authentication import (
    InvalidIngestionKeyError,
    ModelInactiveError,
    authenticate_ingestion_key,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
IngestionKeyHeader = Annotated[
    str | None,
    Header(alias="X-DriftSentry-Key", convert_underscores=False),
]


async def get_authenticated_model(
    session: DatabaseSession,
    ingestion_key: IngestionKeyHeader = None,
) -> RegisteredModel:
    if ingestion_key is None:
        raise _authentication_error("An ingestion key is required")
    try:
        return await authenticate_ingestion_key(session, ingestion_key)
    except InvalidIngestionKeyError as error:
        raise _authentication_error("The ingestion key is invalid") from error
    except ModelInactiveError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "model_inactive", "message": "The model is not active"},
        ) from error


def _authentication_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "invalid_ingestion_key", "message": message},
        headers={"WWW-Authenticate": "ApiKey"},
    )


AuthenticatedModel = Annotated[RegisteredModel, Depends(get_authenticated_model)]
