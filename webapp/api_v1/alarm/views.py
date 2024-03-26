from fastapi import APIRouter

from common.constants import Channel
from webapp.api_v1.alarm.crud import get_alarms_for_channel, update_alarm
from webapp.api_v1.alarm.jobs import enqueue_alarm_deleting, enqueue_alarm_setting
from webapp.api_v1.alarm.schemas import ChannelAlarmsSchema, UserAlarmSchema
from webapp.api_v1.common_dependencies import EnsureUserBodyDep, RedisDep, SessionDep

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.put("/set-alarm")
async def set_alarm(
    body: UserAlarmSchema,
    session: SessionDep,
    redis: RedisDep,
    user: EnsureUserBodyDep,
) -> UserAlarmSchema:
    if user.alarm is not None:
        enqueue_alarm_deleting(redis, user)

    result = await update_alarm(session, user, body.alarm)
    if body.alarm is not None:
        enqueue_alarm_setting(redis, user, body.alarm)

    return result


@router.get("/get-alarms/{channel}")
async def get_alarms(
    channel: Channel,
    session: SessionDep,
) -> list[ChannelAlarmsSchema]:
    return await get_alarms_for_channel(session, channel)
