from fastapi import APIRouter

from common.constants import Channel
from webapp.api_v1.alarm.crud import update_alarm
from webapp.api_v1.alarm.jobs import enqueue_alarm_setting
from webapp.api_v1.alarm.schemas import IsNewUserSchema, UserAlarmSchema
from webapp.api_v1.common_dependencies import (
    EnsureUserBodyDep,
    FindUserQueryDep,
    RedisDep,
    SessionDep,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/set-alarm")
async def set_alarm(
    body: UserAlarmSchema,
    session: SessionDep,
    redis: RedisDep,
    user: EnsureUserBodyDep,
) -> UserAlarmSchema:
    if user.alarm and body.alarm:
        await enqueue_alarm_setting(redis, user, None)

    result = await update_alarm(session, user, body.alarm)
    await enqueue_alarm_setting(redis, user, body.alarm)

    return result


@router.get("/is-new-user")
async def is_new_user(
    channel: Channel,
    channel_id: int,
    session: SessionDep,
    user: FindUserQueryDep,
) -> IsNewUserSchema:
    return IsNewUserSchema(is_new=bool(user is None))
