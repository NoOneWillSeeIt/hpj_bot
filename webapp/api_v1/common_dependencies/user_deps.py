from typing import Annotated

from fastapi import Body, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.api_v1.common_dependencies.schemas import UserMixinSchema
from webapp.api_v1.common_dependencies.session_deps import SessionDep
from webapp.core.constants import Channel
from webapp.core.models import User as UserModel


async def get_user(
    session: AsyncSession, channel: Channel, channel_id: int
) -> UserModel | None:
    stmt = (
        select(UserModel)
        .where(UserModel.channel == channel)
        .where(UserModel.channel_id == channel_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession, channel: Channel, channel_id: int
) -> UserModel:
    if not (db_user := await get_user(session, channel, channel_id)):
        db_user = UserModel(channel=channel, channel_id=channel_id)
        session.add(db_user)
        await session.commit()

    return db_user


async def find_user_query_dep(
    session: SessionDep,
    channel: Annotated[Channel, Query()],
    channel_id: Annotated[int, Query()],
) -> UserModel | None:
    return await get_user(session, channel, channel_id)


async def ensure_user_body_dep(
    session: SessionDep, body: Annotated[UserMixinSchema, Body()]
) -> UserModel:
    return await get_or_create_user(session, body.user.channel, body.user.channel_id)
