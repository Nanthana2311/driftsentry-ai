from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from driftsentry_api.db.session import async_session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
