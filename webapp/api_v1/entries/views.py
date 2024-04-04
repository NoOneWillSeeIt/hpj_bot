from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from common.constants import MSK_TIMEZONE_OFFSET, Channel
from webapp.api_v1.common_dependencies import (
    EnsureUserBodyDep,
    FindUserQueryDep,
    RedisDep,
    SessionDep,
)
from webapp.api_v1.entries.crud import get_entry, write_entry
from webapp.api_v1.entries.jobs import enqueue_report_order
from webapp.api_v1.entries.schemas import (
    EntryBaseSchema,
    EntrySaveSchema,
    FormattedDate,
    ReportOrder,
)

router = APIRouter(prefix="/entries", tags=["entries"])


@router.put("/save-entry")
async def save_entry(
    body: EntrySaveSchema,
    session: SessionDep,
    user: EnsureUserBodyDep,
) -> EntryBaseSchema:
    db_entry = await write_entry(session, user.id, body)
    return EntryBaseSchema(date=db_entry.date, entry=db_entry.entry)


@router.get("/entry")
async def read_entry(
    channel: Channel,
    channel_id: int,
    date: FormattedDate,
    session: SessionDep,
    user: FindUserQueryDep,
) -> EntryBaseSchema:
    db_entry = await get_entry(session, user.id, date)
    if not db_entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entry not exist")
    return EntryBaseSchema(date=db_entry.date, entry=db_entry.entry)


@router.get("/report")
async def get_report(
    channel: Channel,
    channel_id: int,
    redis: RedisDep,
    user: FindUserQueryDep,
    start_date: FormattedDate | None = None,
    end_date: FormattedDate | None = None,
) -> ReportOrder:
    await enqueue_report_order(redis, user, start_date, end_date)
    return ReportOrder(
        accepted_at=datetime.now(tz=MSK_TIMEZONE_OFFSET).strftime("%H:%M:%S")
    )
