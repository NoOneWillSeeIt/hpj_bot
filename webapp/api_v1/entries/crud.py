from sqlalchemy import select, update
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.api_v1.entries.schemas import EntrySaveSchema
from webapp.core.models import JournalEntry


async def get_entries(
    session: AsyncSession, user_id: int, dates: list[str]
) -> list[JournalEntry]:
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.user_id == user_id)
        .where(JournalEntry.date.in_(dates))
    )

    result: Result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_entry(
    session: AsyncSession, user_id: int, date: str
) -> JournalEntry | None:
    res = await get_entries(session, user_id, [date])
    return res[0] if res else None


async def write_entry(
    session: AsyncSession, user_id: int, entry_in: EntrySaveSchema
) -> JournalEntry:
    db_entry = await get_entry(session, user_id, entry_in.date)
    if db_entry:
        stmt = (
            update(JournalEntry)
            .where(JournalEntry.id == db_entry.id)
            .values(entry=entry_in.entry)
        )
        await session.execute(stmt)
    else:
        db_entry = JournalEntry(user_id=user_id, entry=entry_in.entry, date=entry_in.date)
        session.add(db_entry)

    await session.commit()
    return db_entry
