import asyncio
from concurrent.futures import ProcessPoolExecutor
import functools
import logging
from typing import Callable
from telegram.ext import ContextTypes

from tg_bot.commands import HPJCommands
from tg_bot.constants import FLASK_PIC_PATH
import tg_bot.db.aio_queries as asyncdb
from tg_bot.jobs.workers import create_weekly_report, drop_entries, mark_entries_for_delete


async def reminder(context: ContextTypes.DEFAULT_TYPE):
    """Reminds user about journal filling the journal."""
    if not context.chat_data.get('survey'):
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=f'Привет, время заполнить журнал. Напиши /{HPJCommands.ADD_ENTRY} и вперёд!'
        )
    else:
        logging.info(f'Alarm cancelled by survey {context.chat_data}')


async def weekly_report(context: ContextTypes.DEFAULT_TYPE):
    """Creates weekly reports and sends it to users."""
    logging.info('Started building weekly report')
    loop = asyncio.get_event_loop()
    chat_ids = await asyncdb.read_chats_with_entries(context.bot_data)
    with ProcessPoolExecutor(max_workers=4) as pool:
        tasks = [
            loop.run_in_executor(pool, create_weekly_report, chat, context.bot_data['db_path'])
            for chat in chat_ids
        ]

        for future_result in asyncio.as_completed(tasks):
            report = await future_result
            if not report.file_bytes:
                logging.info(f'{report.chat_id} has no entries from last week')
                continue

            message = await context.bot.send_document(
                report.chat_id, document=report.file_bytes,
                caption=f'Твой дневник за неделю {report.period}', disable_notification=True,
                filename=report.filename, thumbnail=FLASK_PIC_PATH
            )
            await message.pin(disable_notification=True)

    pool.shutdown()
    logging.info('Finished building weekly report')


async def _no_result_all_chat_job_executor(context: ContextTypes.DEFAULT_TYPE, func: Callable):
    """Execute provided worker function on all users.

    Args:
        context (ContextTypes.DEFAULT_TYPE): telegram.Context
        func (Callable): Worker function to apply.
    """
    chat_ids = await asyncdb.read_chats_with_entries(context.bot_data)
    with ProcessPoolExecutor(max_workers=4) as pool:
        pool.map(func, chat_ids, chunksize=1)


async def mark_old_entries_to_delete(context: ContextTypes.DEFAULT_TYPE):
    """Moves old entries to del_journal table if entries older than constants.DAYS_TO_STORE"""
    await _no_result_all_chat_job_executor(
        context,
        functools.partial(mark_entries_for_delete, context.bot_data['db_path']),
    )


async def drop_outdated_entries(context: ContextTypes.DEFAULT_TYPE):
    """Deletes old entries from del_journal table if they were added more than
    constants.DAYS_TO_STORE_BACKUP days"""
    await _no_result_all_chat_job_executor(
        context,
        functools.partial(drop_entries, context.bot_data['db_path']),
    )