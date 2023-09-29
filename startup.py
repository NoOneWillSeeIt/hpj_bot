from datetime import datetime
import logging
import os
import sqlite3

from telegram import Update

from bot import SURVEY_JOB_PREFIX, configure_app, reminder


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


DB_FOLDER = 'db_instance'
DB_PATH = f'{DB_FOLDER}/hpj_bot.db'


def main():
    app = configure_app()

    dirs = os.listdir()
    if not DB_FOLDER in dirs:
        os.mkdir(DB_FOLDER)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    table_exists = cur.execute('''
        SELECT EXISTS(
            SELECT 1
            FROM sqlite_schema
            WHERE type = 'table' AND name = 'journal'
        )
    ''').fetchone()[0]

    if not table_exists:
        cur.execute('''
            CREATE TABLE journal(chat_id BIGINT PRIMARY KEY, entries TEXT, alarm TEXT);
        ''')
        cur.execute('''
            CREATE UNIQUE INDEX journal_chat_id ON journal(chat_id);
        ''')

        conn.commit()

    chat_alarms = cur.execute('''
        SELECT chat_id, alarm
        FROM journal
        WHERE alarm IS NOT NULL
    ''')

    for row in chat_alarms.fetchall():
        try:
            chat_id = row[0]
            time = datetime.strptime(row[1], '%H:%M%z').timetz()
            job_name = f'{SURVEY_JOB_PREFIX}{chat_id}'
            app.job_queue.run_daily(reminder, time, name=job_name, chat_id=chat_id)

        except (ValueError, IndexError) as ex:
            logging.warning(f'Job setting failed: {ex}')
            raise

    app.bot_data['db_conn'] = conn
    app.bot_data['db_path'] = DB_PATH

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
