from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.constants import Channel
from webapp.api_v1.alarm.schemas import UserAlarmSchema
from webapp.api_v1.common_dependencies.schemas import UserChannelSchema
from webapp.core.models import JournalEntry, User


async def update_alarm(
    session: AsyncSession, user: User, alarm: str | None
) -> UserAlarmSchema:
    user.alarm = alarm
    await session.commit()
    return UserAlarmSchema(
        alarm=user.alarm,
        user=UserChannelSchema(
            channel=Channel(user.channel), channel_id=user.channel_id
        ),
    )


async def has_entries(session: AsyncSession, user: User) -> bool:
    stmt = select(
        (select(JournalEntry).where(JournalEntry.user_id == user.id)).exists()
    )

    return bool(await session.scalar(stmt))
