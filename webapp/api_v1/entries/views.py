from fastapi import APIRouter, HTTPException, status

from webapp.api_v1.common_dependencies import (
    EnsureUserBodyDep,
    FindUserQueryDep,
    SessionDep,
)
from webapp.api_v1.entries.crud import get_entry, write_entry
from webapp.api_v1.entries.schemas import (
    EntryBaseSchema,
    EntrySaveSchema,
    FormattedDate,
)
from webapp.core.constants import Channel

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
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Entry not exist')
    return EntryBaseSchema(date=db_entry.date, entry=db_entry.entry)
