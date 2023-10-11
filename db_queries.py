
from datetime import time
import json
import logging
import sqlite3
from typing import Optional

from hpj_questions import Questions


def get_db_conn_from_bot_data(bot_data: dict) -> sqlite3.Connection:
    try:
        conn = bot_data['db_conn']
        conn.cursor()
    except Exception as ex:
        logging.warning(f'DB conn was dead. Trying to restore. ex: {ex}')
        conn = sqlite3.connect(bot_data['db_path'])
        bot_data['db_conn'] = conn

    return conn


async def _awaitable_execute(cursor: sqlite3.Cursor, sql: str, params: dict) -> sqlite3.Cursor:
    return cursor.execute(sql, params)


async def write_alarm(bot_data: dict, chat_id: int, time: time):
    conn = get_db_conn_from_bot_data(bot_data)
    time_str = time.strftime('%H:%M%z')
    await _awaitable_execute(
        conn.cursor(),
        '''
        INSERT INTO journal(chat_id, alarm) VALUES(:chat_id, :alarm)
        ON CONFLICT(chat_id) DO UPDATE SET alarm = excluded.alarm;
        ''',
        {'chat_id': chat_id, 'alarm': time_str}
    )
    logging.info(f'DB saved alarm for {chat_id} on {time_str}')
    conn.commit()


async def clear_alarm(bot_data: dict, chat_id: int):
    conn = get_db_conn_from_bot_data(bot_data)
    await _awaitable_execute(
        conn.cursor(),
        '''
        UPDATE journal
        SET alarm = NULL
        WHERE chat_id = :chat_id;
        ''',
        {'chat_id': chat_id}
    )
    logging.info(f'DB dropped alarm for {chat_id}')
    conn.commit()


async def write_entry(bot_data: dict, chat_id: int, entry: dict):
    conn = get_db_conn_from_bot_data(bot_data)
    date = entry.get(Questions.Date.name)
    await _awaitable_execute(
        conn.cursor(),
        '''
        INSERT INTO journal(chat_id, entries)
        VALUES
        (
            :chat_id,
            json_object(
                :date,
                json(:entry)
            )
        ) ON CONFLICT(chat_id) DO
        UPDATE
        SET
        entries = json_set(
            coalesce(entries, '{}'),
            '$.' || '"' || :date || '"', -- to make key like $."23.04" and not split into '23':{'04'
            json(:entry)
        );
        ''',
        {'chat_id': chat_id,
         'date': date,
         'entry': json.dumps(entry, ensure_ascii=False)}
    )
    logging.info(f'DB saved new entry for {chat_id}')
    conn.commit()


async def read_entries(bot_data: dict, chat_id: str) -> Optional[dict]:
    conn = get_db_conn_from_bot_data(bot_data)
    cursor = await _awaitable_execute(
        conn.cursor(),
        '''
        SELECT coalesce(entries, '{}')
        FROM journal
        WHERE chat_id = :chat_id;
        ''',
        {'chat_id': chat_id}
    )
    str_entries = cursor.fetchone()[0]
    logging.info(f'DB read entries for {chat_id}')
    return json.loads(str_entries)


def check_table_exists(conn: sqlite3.Connection) -> bool:
    return conn.cursor().execute('''
            SELECT EXISTS(
                SELECT 1
                FROM sqlite_schema
                WHERE type = 'table' AND name = 'journal'
            )
    ''').fetchone()[0]


def create_base_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE journal(chat_id BIGINT PRIMARY KEY, entries TEXT, alarm TEXT);
    ''')
    cur.execute('''
        CREATE UNIQUE INDEX journal_chat_id ON journal(chat_id);
    ''')

    cur.close()
    conn.commit()


def get_all_chat_alarms(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    cur.row_factory = sqlite3.Row
    chat_alarms = cur.execute('''
        SELECT chat_id, alarm
        FROM journal
        WHERE alarm IS NOT NULL
    ''')

    return chat_alarms.fetchall()
