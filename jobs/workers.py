from collections import namedtuple
import datetime

from constants import ENTRY_KEY_FORMAT, JINJA_TEMPLATE_PATH, JOURNAL_TEMPLATE
import db.queries as db
from hpj_questions import Questions
from journal_view import HTMLGenerator


WeeklyReport = namedtuple(
    'WeeklyReport', ['chat_id', 'period', 'filename', 'file_bytes']
)


def create_weekly_report(chat_id: str, db_path: str) -> WeeklyReport:
    entries = db.read_entries(db_path, chat_id)
    today = datetime.datetime.today()
    last_sunday = today - datetime.timedelta(days=today.isoweekday())
    last_week = [
        (last_sunday - datetime.timedelta(days=day_diff)).strftime(ENTRY_KEY_FORMAT)
        for day_diff in range(6, -1, -1)
    ]

    result_entries = {}
    for date in last_week:
        entry = entries.get(date)
        if entry:
            result_entries[date] = entry

    # TODO: NO DELETING ON CURRENT ITERATION
    # db.mark_entries_for_delete(db_path, chat_id, last_week)
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
