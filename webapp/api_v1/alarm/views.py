from fastapi import APIRouter

from webapp.api_v1.alarm.crud import get_alarms_for_channel, update_alarm
from webapp.api_v1.alarm.schemas import ChannelAlarmsSchema, UserAlarmSchema
from webapp.api_v1.common_dependencies import EnsureUserBodyDep, SessionDep
from webapp.core.constants import Channel

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.put("/set-alarm")
async def set_alarm(
    body: UserAlarmSchema,
    session: SessionDep,
    user: EnsureUserBodyDep,
) -> UserAlarmSchema:
    return await update_alarm(session, user, body.alarm)


@router.get("/get-alarms/{channel}")
async def get_alarms(
    channel: Channel,
    session: SessionDep,
) -> list[ChannelAlarmsSchema]:
    return await get_alarms_for_channel(session, channel)
