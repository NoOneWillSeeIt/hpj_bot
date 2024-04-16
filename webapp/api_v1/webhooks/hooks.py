from typing import Annotated
from fastapi import APIRouter, File, Form
from pydantic import BaseModel

from common.constants import ReportRequester


router = APIRouter()


class ChannelAlarms(BaseModel):
    channel_ids: list[int]
    time: str


class Report(BaseModel):
    channel_id: Annotated[int, Form()]
    requester: Annotated[ReportRequester, Form()]
    start_date: Annotated[str, Form()]
    end_date: Annotated[str, Form()]
    file: Annotated[bytes, File()]


@router.post("channel-alarm")
async def alarm(body: ChannelAlarms):
    """
    Notifies channel-app when its users needs to be alarmed.
    """


@router.post("channel-weekly-report")
async def weekly_report(body: Report):
    """
    Weekly sends generated reports for users in particular channel.
    """
