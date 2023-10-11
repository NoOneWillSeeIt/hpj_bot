from telegram.ext import ContextTypes

from commands.commands import HPJCommands


async def reminder(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f'Привет, нужно заполнить журнал. Напиши /{HPJCommands.ADD_ENTRY} и вперёд!'
    )
