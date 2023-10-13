
from datetime import time
import json
import logging
import sqlite3
from typing import Optional

import aiosqlite
from constants import TIME_FORMAT


async def get_db_conn_from_bot_data(bot_data: dict) -> aiosqlite.Connection:
    try:
        conn = bot_data['db_conn']
        await conn.cursor()
    except Exception as ex:
        logging.warning(f'DB conn was dead. Trying to restore. ex: {ex}')
        conn = await aiosqlite.connect(bot_data['db_path'])
        bot_data['db_conn'] = conn

    return conn


async def write_alarm(bot_data: dict, chat_id: int, time: time):
    conn = await get_db_conn_from_bot_data(bot_data)
    time_str = time.strftime(TIME_FORMAT)
    await conn.execute(
        '''
        INSERT INTO journal(chat_id, alarm) VALUES(:chat_id, :alarm)
        ON CONFLICT(chat_id) DO UPDATE SET alarm = excluded.alarm;
        ''',
        {'chat_id': chat_id, 'alarm': time_str}
    )
    logging.info(f'DB saved alarm for {chat_id} on {time_str}')
    await conn.commit()


async def clear_alarm(bot_data: dict, chat_id: int):
    conn = await get_db_conn_from_bot_data(bot_data)
    await conn.execute(
        '''
        UPDATE journal
        SET alarm = NULL
        WHERE chat_id = :chat_id;
        ''',
        {'chat_id': chat_id}
    )
    logging.info(f'DB dropped alarm for {chat_id}')
    await conn.commit()


async def write_entry(bot_data: dict, chat_id: int, key: str, entry: dict):
    conn = await get_db_conn_from_bot_data(bot_data)
    await conn.execute(
        '''
        INSERT INTO journal(chat_id, entries)
        VALUES
        (
            :chat_id,
            json_object(
                :key,
                json(:entry)
            )
        ) ON CONFLICT(chat_id) DO
        UPDATE
        SET
        entries = json_set(
            coalesce(entries, '{}'),
            '$.' || '"' || :key || '"', -- to make key like $."23.04" and not split into '23':{'04'
            json(:entry)
        );
        ''',
        {'chat_id': chat_id,
         'key': key,
         'entry': json.dumps(entry, ensure_ascii=False)}
    )
    logging.info(f'DB saved new entry for {chat_id}')
    await conn.commit()


async def read_entries(bot_data: dict, chat_id: str) -> Optional[dict]:
    conn = await get_db_conn_from_bot_data(bot_data)
    cursor = await conn.execute(
        '''
        SELECT coalesce(entries, '{}')
        FROM journal
        WHERE chat_id = :chat_id;
        ''',
        {'chat_id': chat_id}
    )
    str_entries = await cursor.fetchone()
    str_entries = str_entries[0] if str_entries else '{}'
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
    conn.execute('''
        CREATE TABLE journal(chat_id BIGINT PRIMARY KEY, entries TEXT, alarm TEXT);
    ''')
    conn.execute('''
        CREATE UNIQUE INDEX journal_chat_id ON journal(chat_id);
    ''')
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
