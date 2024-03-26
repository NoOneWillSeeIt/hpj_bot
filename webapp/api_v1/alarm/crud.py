from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.constants import Channel
from webapp.api_v1.alarm.schemas import ChannelAlarmsSchema, UserAlarmSchema
from webapp.core.models import User


async def update_alarm(
    session: AsyncSession, user: User, alarm: str | None
) -> UserAlarmSchema:
    user.alarm = alarm
    await session.commit()
    return UserAlarmSchema(
        alarm=user.alarm, user={"channel": user.channel, "channel_id": user.channel_id}
    )


async def get_alarms_for_channel(
    session: AsyncSession, channel: Channel
) -> list[ChannelAlarmsSchema]:
    stmt = (
        select(User.channel_id, User.alarm)
        .where(User.channel == channel)
        .where(User.alarm is not None)
    )
    result = await session.execute(stmt)
    return list(result.all())
