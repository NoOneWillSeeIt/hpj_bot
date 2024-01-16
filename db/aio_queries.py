from datetime import time
import json
import logging

import aiosqlite
from constants import TIME_FORMAT


async def get_db_conn_from_bot_data(bot_data: dict) -> aiosqlite.Connection:
    """Returns connection to database from bot_data. Uses existing connection from 'db_conn' key if
    it's alive or creates a new one from 'db_path'.

    Args:
        bot_data (dict): bot_data initialized on post_init app configuration.
        Must contain 'db_path' key to establish connection.

    Returns:
        aiosqlite.Connection: Connection to DB.
    """
    try:
        conn = bot_data['db_conn']
        await conn.cursor()
    except Exception as ex:
        logging.warning(f'DB conn was dead. Trying to restore. ex: {ex}')
        conn = await aiosqlite.connect(bot_data['db_path'])
        bot_data['db_conn'] = conn

    return conn


async def write_alarm(bot_data: dict, chat_id: int, time: time):
    """Write alarm to DB.

    Args:
        bot_data (dict): bot_data initialized on post_init app configuration.
        chat_id (int): chat_id from journal table.
        time (time): Alarm time.
    """
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
    """Drop alarm time.

    Args:
        bot_data (dict): bot_data initialized on post_init app configuration.
        chat_id (int): chat_id from journal table.
    """
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
    """Write new entry to journal. Journal stores as JSON with date keys.

    Args:
        bot_data (dict): bot_data initialized on post_init app configuration.
        chat_id (int): chat_id from journal table.
        key (str): Date key to store entry.
        entry (dict): Prepared question replies.
    """
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


async def read_entries(bot_data: dict, chat_id: str) -> dict:
    """Returns all entries of selected user.

    Args:
        bot_data (dict): bot_data initialized on post_init app configuration.
        chat_id (str): chat_id from journal table.

    Returns:
        dict: User entries.
    """
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


async def read_chats_with_entries(bot_data: dict) -> list:
    """Returns list of chat_id with entries.

    Args:
        bot_data (dict): _description_

    Returns:
        list: _description_
    """
    conn = await get_db_conn_from_bot_data(bot_data)
    cursor = await conn.execute(
        '''
        SELECT chat_id
        FROM journal
        WHERE entries IS NOT NULL and json(entries) != json('{}');
        ''',
    )
    logging.info('DB read entries all chats with entries')
    chat_ids = await cursor.fetchall()
    return [tup[0] for tup in chat_ids]


async def is_new_user(bot_data: dict, chat_id: str) -> bool:
    """Returns if user already exists in DB.

    Args:
        bot_data (dict): bot_data initialized on post_init app configuration.
        chat_id (str): chat_id from journal table.

    Returns:
        bool: Is user exists in DB.
    """
    conn = await get_db_conn_from_bot_data(bot_data)
    cursor = await conn.execute(
        '''
        SELECT NOT EXISTS(
            SELECT 1
            FROM journal
            WHERE chat_id = :chat_id
                AND entries IS NOT NULL
        )
        ''',
        {'chat_id': chat_id}
    )
    result = await cursor.fetchone()
    return bool(result[0])
