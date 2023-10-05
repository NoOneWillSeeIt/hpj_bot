from datetime import datetime
import logging
import os
import sqlite3

from telegram import Update

from bot import configure_app
from constants import ALARM_JOB_PREFIX, DB_FOLDER, DB_PATH
import db_queries as db
from jobs import reminder as job_reminder


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    app = configure_app()

    dirs = os.listdir()
    if not DB_FOLDER in dirs:
        os.mkdir(DB_FOLDER)

    conn = sqlite3.connect(DB_PATH)

    if not db.check_table_exists(conn):
        db.create_base_table(conn)

    for row in db.get_all_chat_alarms(conn):
        try:
            chat_id = row['chat_id']
            time = datetime.strptime(row['alarm'], '%H:%M%z').timetz()
            job_name = f'{ALARM_JOB_PREFIX}{chat_id}'
            app.job_queue.run_daily(job_reminder, time, name=job_name, chat_id=chat_id)

        except (ValueError, KeyError) as ex:
            logging.warning(f'Alarm job setting failed: {ex}')
            raise

    app.bot_data['db_conn'] = conn
    app.bot_data['db_path'] = DB_PATH

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
