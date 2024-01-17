from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from commands import HPJCommands
from constants import DAYS_TO_STORE


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я буду вести дневник твоих головных болей.\n'
                                    'Заполнять его нужно перед сном. Чтобы не забывать можешь '
                                    'поставить напоминание через команду /alarm чч:мм')


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'/{HPJCommands.ALARM} - установить напоминание о заполнении - я сам тебе напишу.'
        ' Время нужно указать по Москве, т.к. твой часовой пояс для меня загадка.\n\n'
        f'/{HPJCommands.ADD_ENTRY} - начать заполнение опросника. Можно заполнить за любой день,'
        ' достаточно лишь указать дату в формате дд.мм\n\n'
        f'/{HPJCommands.LOAD} - выгрузить все сохранённые записи. Срок хранения - {DAYS_TO_STORE}'
        ' дней. Более ранние записи будут удаляться автоматически. Помимо этого в начале недели я'
        ' буду присылать тебе отчёт за прошедшие 7 дней. Увед будет тихим и сообщение будет'
        ' закреплено.\n\n'
        f'/{HPJCommands.CANCEL} - отменить подписку на уведы. Я тебе перестану писать, но'
        ' буду хранить то, что было заполнено.\n\n'
        'Все эти команды доступны в меню\n↓'
    )


START_HANDLER = CommandHandler(HPJCommands.START, start)
HELP_HANDLER = CommandHandler(HPJCommands.HELP, help_handler)
