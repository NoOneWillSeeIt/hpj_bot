from typing import List

from telegram import Update
from telegram.ext import BaseHandler, CommandHandler, ContextTypes

from commands import HPJCommands


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я буду вести дневник твоих головных болей.\n'
                                    'Заполнять его нужно перед сном. Чтобы не забывать можешь '
                                    'поставить напоминание через команду /alarm чч:мм')


def get_handlers() -> List[BaseHandler]:
    return [
        CommandHandler(HPJCommands.START, start),
    ]
