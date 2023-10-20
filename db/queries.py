import json
import logging
import sqlite3
from typing import List


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


def read_entries(db_path: str, chat_id: str) -> dict:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            '''
            SELECT coalesce(entries, '{}')
            FROM journal
            WHERE chat_id = :chat_id;
            ''',
            {'chat_id': chat_id}
        )
        str_entries = cursor.fetchone()
        str_entries = str_entries[0] if str_entries else '{}'
        logging.info(f'DB read entries for {chat_id}')
    return json.loads(str_entries)


def mark_entries_for_delete(db_path: str, chat_id: str, keys: List[str]):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            WITH cte AS (
                SELECT json_each.value AS key
                FROM json_each(:keys)
            )
            UPDATE journal
            SET entries = json_set(
                json_set(
                    entries,
                    '$.' || '"del_' || cte.key || '"',
                    json(entries -> '$.' || '"' || cte.key || '"')
                ),
                '$.' || '"' || cte.key || '"',
                NULL
            )
            FROM cte
            WHERE chat_id = :chat_id;
            ''',
            {'chat_id': chat_id,
             'keys': keys}
        )
        logging.info(f'DB marked deleted entries for dates {keys} and chat_id {chat_id}')
