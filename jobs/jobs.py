import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
from telegram.ext import ContextTypes

from commands import HPJCommands
from constants import FLASK_PIC_PATH
import db.aio_queries as asyncdb
from .workers import create_weekly_report


async def reminder(context: ContextTypes.DEFAULT_TYPE):
    if not context.chat_data.get('survey'):
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=f'Привет, время заполнить журнал. Напиши /{HPJCommands.ADD_ENTRY} и вперёд!'
        )
    else:
        logging.info(f'ALARM CANCELLED BY SURVEY {context.chat_data}')


async def weekly_report(context: ContextTypes.DEFAULT_TYPE):
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
            message = await context.bot.send_document(
                report.chat_id, document=report.file_bytes,
                caption=f'Твой дневник за неделю {report.period}', disable_notification=True,
                filename=report.filename, thumbnail=FLASK_PIC_PATH
            )
            await message.pin(disable_notification=True)

    pool.shutdown()
    logging.info('Finished building weekly report')
