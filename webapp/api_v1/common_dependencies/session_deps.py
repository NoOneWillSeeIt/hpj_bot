from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.core import db_helper, redis_helper

SessionDep = Annotated[AsyncSession, Depends(db_helper.async_session_dependency)]
RedisDep = Annotated[AsyncRedis, Depends(redis_helper.async_redis_dependency)]
