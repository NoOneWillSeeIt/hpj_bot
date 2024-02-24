from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.core import db_helper

SessionDep = Annotated[AsyncSession, Depends(db_helper.async_session_dependency)]
