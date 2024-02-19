from datetime import datetime, timedelta, time
import logging
import os
import sqlite3

from telegram import Update

from tg_bot.bot import configure_app
from tg_bot.constants import ALARM_JOB_PREFIX, DB_FOLDER, DB_PATH, MSK_TIMEZONE_OFFSET, TIME_FORMAT
import tg_bot.db.queries as db
from tg_bot.jobs import reminder, weekly_report
from tg_bot.jobs.jobs import drop_outdated_entries, mark_old_entries_to_delete


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def nearest_weekday(day=0):
    today = datetime.today()
    diff = timedelta(days=(day - today.weekday()) % 7)
    return today + diff


def main():
    """
    Configure app, create database if not exists, add scheduling jobs to bot and run it.
    TODO: add cmd line args to use test token instead of prod for testing purposes
    """
    app = configure_app()

    dirs = os.listdir()
    if DB_FOLDER not in dirs:
        os.mkdir(DB_FOLDER)

    conn = sqlite3.connect(DB_PATH)

    if not db.check_base_table_exists(conn):
        db.create_base_table(conn)

    if not db.check_del_tmp_table_exists(conn):
        db.create_del_tmp_table(conn)

    for row in db.get_all_chat_alarms(conn):
        try:
            chat_id = row['chat_id']
            alarm_time = datetime.strptime(row['alarm'], TIME_FORMAT).timetz()
            job_name = f'{ALARM_JOB_PREFIX}{chat_id}'
            app.job_queue.run_daily(reminder, alarm_time, name=job_name, chat_id=chat_id)

        except (ValueError, KeyError) as ex:
            logging.warning(f'Alarm job setting failed: {ex}')
            raise

    conn.close()

    nearest_monday = nearest_weekday(0).replace(hour=23, minute=0, second=0, microsecond=0,
                                                tzinfo=MSK_TIMEZONE_OFFSET)
    app.job_queue.run_repeating(
        weekly_report, timedelta(days=7), first=nearest_monday, name='weekly_report'
    )
    app.job_queue.run_repeating(
        mark_old_entries_to_delete, timedelta(days=7), first=nearest_monday,
        name='mark_old_entries_to_delete'
    )
    app.job_queue.run_monthly(
        drop_outdated_entries, time(hour=23, minute=0, tzinfo=MSK_TIMEZONE_OFFSET), day=1,
        name='drop_outdated_entries'
    )

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
