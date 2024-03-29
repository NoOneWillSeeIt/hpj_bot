from typing import Annotated
from fastapi import APIRouter, File
from pydantic import BaseModel


router = APIRouter()


class ChannelAlarms(BaseModel):
    channel_ids: list[int]
    time: str


class Report(BaseModel):
    report_file: Annotated[bytes, File()]


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
