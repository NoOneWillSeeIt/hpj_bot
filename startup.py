from datetime import datetime, timedelta
import logging
import os
import sqlite3

from telegram import Update

from bot import configure_app
from constants import ALARM_JOB_PREFIX, DB_FOLDER, DB_PATH, MSK_TIMEZONE_OFFSET, TIME_FORMAT
import db.queries as db
from jobs import reminder, weekly_report


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
    app = configure_app()

    dirs = os.listdir()
    if DB_FOLDER not in dirs:
        os.mkdir(DB_FOLDER)

    conn = sqlite3.connect(DB_PATH)

    if not db.check_table_exists(conn):
        db.create_base_table(conn)

    for row in db.get_all_chat_alarms(conn):
        try:
            chat_id = row['chat_id']
            time = datetime.strptime(row['alarm'], TIME_FORMAT).timetz()
            job_name = f'{ALARM_JOB_PREFIX}{chat_id}'
            app.job_queue.run_daily(reminder, time, name=job_name, chat_id=chat_id)

        except (ValueError, KeyError) as ex:
            logging.warning(f'Alarm job setting failed: {ex}')
            raise

    conn.close()

    nearest_monday = nearest_weekday(0)
    nearest_monday.replace(hour=20, minute=0, second=0, microsecond=0, tzinfo=MSK_TIMEZONE_OFFSET)
    app.job_queue.run_repeating(weekly_report, timedelta(days=7), first=nearest_monday,
                                name='weekly_report')

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
