import json
import logging
import sqlite3
from typing import List, Set

from constants import DAYS_TO_STORE_BACKUP


def check_table_exists(conn: sqlite3.Connection, tbl_name: str) -> bool:
    return conn.execute('''
        SELECT EXISTS(
            SELECT 1
            FROM sqlite_schema
            WHERE type = 'table' AND name = :name
        )
    ''', {'name': tbl_name}).fetchone()[0]


def check_base_table_exists(conn: sqlite3.Connection) -> bool:
    return check_table_exists(conn, 'journal')


def check_del_tmp_table_exists(conn: sqlite3.Connection) -> bool:
    return check_table_exists(conn, 'del_journal')


def create_base_table(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE journal(
                 chat_id BIGINT PRIMARY KEY,
                 entries TEXT,
                 alarm TEXT
        );
    ''')
    conn.execute('''
        CREATE UNIQUE INDEX journal_chat_id ON journal(chat_id);
    ''')
    conn.commit()


def create_del_tmp_table(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE del_journal(
                 r_id INTEGER PRIMARY KEY ASC,
                 chat_id BIGINT,
                 entries TEXT,
                 mark_date TEXT,
                 FOREIGN KEY(chat_id) REFERENCES journal(chat_id) ON DELETE CASCADE
        );
    ''')
    conn.execute('''
        CREATE INDEX del_journal_date ON del_journal(chat_id, mark_date);
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


def delete_marked_entries(db_path: str, chat_id: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            DELETE FROM del_journal
            WHERE
                chat_id = :chat_id
                AND mark_date < datetime('now', '-' || :store_time || ' days');
            ''',
            {
                'chat_id': chat_id,
                'store_time': DAYS_TO_STORE_BACKUP,
            }
        )


def read_entries_keys(db_path: str, chat_id: str) -> Set[str]:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            '''
            SELECT json_each.key
            FROM journal, json_each(entries)
            WHERE journal.chat_id = :chat_id
            ''',
            {'chat_id': chat_id}
        )
        keys = {tup[0] for tup in cursor.fetchall()}
    return keys


def mark_entries_for_delete(db_path: str, chat_id: str, keys: List[str]) -> None:
    with sqlite3.connect(db_path) as conn:
        marked_for_delete = conn.execute(
            '''
            WITH keys AS (
                SELECT json_each.value AS key
                FROM json_each(:keys)
            ), outdated_entries AS (
                SELECT json_group_object(json_each.key, json_each.value)
                FROM journal, json_each(entries)
                WHERE
                    journal.chat_id = :chat_id
                    AND json_each.key IN (SELECT key FROM keys)
            )
            INSERT INTO del_journal(chat_id, entries, mark_date)
            VALUES(:chat_id, json((SELECT * FROM outdated_entries)), datetime())
            RETURNING *;
            ''',
            {
                'chat_id': chat_id,
                'keys': json.dumps(list(keys), ensure_ascii=False)
            }
        )

        if not marked_for_delete.fetchone():
            logging.warning(f'No entries were marked for delete chat_id={chat_id}')
            return

        conn.execute(
            '''
            WITH keys AS (
                SELECT json_each.value AS key
                FROM json_each(:keys)
            ), replaced_entries AS (
                SELECT json_group_object(json_each.key, json_each.value)
                FROM journal, json_each(entries)
                WHERE
                    journal.chat_id = :chat_id
                    AND json_each.key NOT IN (SElECT key FROM keys)
            )
            UPDATE journal
            SET
                entries = (
                    SELECT * FROM replaced_entries
                )
            WHERE chat_id = :chat_id;
            ''',
            {
                'chat_id': chat_id,
                'keys': json.dumps(list(keys), ensure_ascii=False)
            }
        )
        logging.info(f'DB marked deleted entries for dates {keys} and chat_id {chat_id}')
