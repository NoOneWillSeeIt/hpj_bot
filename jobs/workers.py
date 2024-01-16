from collections import namedtuple
from datetime import datetime, timedelta

from constants import DAYS_TO_STORE, ENTRY_KEY_FORMAT, JINJA_TEMPLATE_PATH, JOURNAL_TEMPLATE
import db.queries as db
from hpj_questions import Questions
from journal_view import HTMLGenerator


WeeklyReport = namedtuple(
    'WeeklyReport', ['chat_id', 'period', 'filename', 'file_bytes']
)


def create_weekly_report(chat_id: str, db_path: str) -> WeeklyReport:
    """Generates weekly report from last monday to last sunday. Creates report even if there's only
    one entry from last week.

    Args:
        chat_id (str): chat_id from journal table.
        db_path (str): Path to database.

    Returns:
        WeeklyReport: Weekly report. file_bytes=None if there's no entries from last week.
    """
    entries = db.read_entries(db_path, chat_id)
    today = datetime.today()
    last_sunday = today - timedelta(days=today.isoweekday())
    last_week = [
        (last_sunday - timedelta(days=day_diff)).strftime(ENTRY_KEY_FORMAT)
        for day_diff in range(6, -1, -1)
    ]

    result_entries = {}
    for date in last_week:
        entry = entries.get(date)
        if entry:
            result_entries[date] = entry

    html_gen = HTMLGenerator(JINJA_TEMPLATE_PATH, JOURNAL_TEMPLATE, enable_async=False)

    period = f'{last_week[0]}-{last_week[-1]}'
    return WeeklyReport(
        chat_id=chat_id,
        period=period,
        filename=html_gen.gen_filename(period),
        file_bytes=(
            html_gen.generate(Questions.to_dict(), result_entries)
            if result_entries
            else None
        )
    )


def mark_entries_for_delete(db_path: str, chat_id: str | int):
    """Moves old entries to del_journal table if entries older than constants.DAYS_TO_STORE.

    Args:
        db_path (str): Path to database.
        chat_id (str | int): chat_id from journal table.
    """
    existing_keys = db.read_entries_keys(db_path, chat_id)
    today = datetime.today()
    keys_to_save = {
        (today - timedelta(days=day_diff)).strftime(ENTRY_KEY_FORMAT)
        for day_diff in range(DAYS_TO_STORE)
    }
    keys_to_delete = existing_keys - keys_to_save
    if not keys_to_delete:
        return

    db.mark_entries_for_delete(db_path, chat_id, keys_to_delete)


def drop_entries(db_path: str, chat_id: str | int):
    """Deletes old entries from del_journal table if they were added more than
    constants.DAYS_TO_STORE_BACKUP days.

    Args:
        db_path (str): Path to database.
        chat_id (str | int): chat_id from journal table.
    """
    db.delete_marked_entries(db_path, chat_id)
