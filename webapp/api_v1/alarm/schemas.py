import datetime
from typing import Annotated

from fastapi import HTTPException, status
from pydantic import AfterValidator, BaseModel

from common.constants import TIME_FMT
from webapp.api_v1.common_dependencies.schemas import UserMixinSchema


def validate_time(time: str | None) -> str | None:
    if time is None:
        return None

    try:
        datetime.datetime.strptime(time, TIME_FMT)
    except ValueError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Wrong time format. Expected: '{TIME_FMT}'",
        )
    return time


FormattedTime = Annotated[str | None, AfterValidator(validate_time)]


class UserAlarmSchema(UserMixinSchema):
    alarm: FormattedTime


class IsNewUserSchema(BaseModel):
    is_new: bool


class ChannelAlarmsSchema(BaseModel):
    channel_id: int
    alarm: str
