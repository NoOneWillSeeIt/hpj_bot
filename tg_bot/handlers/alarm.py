from datetime import datetime

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from tg_bot.commands import HPJCommands
from ..requests import save_alarm

ALARM_CONVO = 0


class AlarmHandlers:
    """Handlers for setting time to notify users."""

    @classmethod
    async def alarm(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Conversation starter. Supports two ways of setting alarm:
        /alarm hh:mm - sets the alarm.
        /alarm - starts convo to set the alarm.
        """
        if not await cls._set_alarm(update, context):
            await update.message.reply_text(
                "Нужно указать время по московскому часовому поясу в виде чч:мм."
            )
            return ALARM_CONVO

        return ConversationHandler.END

    @classmethod
    async def alarm_convo(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Alarm conversation. Conversation ends in any case."""
        if not await cls._set_alarm(update, context):
            await update.message.reply_text(
                f"Неверный формат, попробуй ещё раз нажать /{HPJCommands.ALARM}"
            )

        return ConversationHandler.END

    @classmethod
    async def _set_alarm(
        cls, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """Sets alarm if update.message contains valid time and return True.
        Return False otherwise."""
        try:
            chat_id = update.message.chat_id
            user_input = update.message.text.strip()
            if context.args:
                user_input = context.args[0]

            time = datetime.strptime(user_input, "%H:%M").time()
            await save_alarm(chat_id, time)

            await update.message.reply_text(
                f'Оповещения будут приходить в {time.strftime("%H:%M")}'
            )
        except (ValueError, IndexError):
            return False

        return True

    @classmethod
    async def cancel(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Drop alarm time from table."""
        chat_id = update.message.chat_id
        await save_alarm(chat_id, None)
        await update.message.reply_text(
            "Больше уведомлений не будет. Спасибо за использование, выздоравливай!",
            reply_markup=ReplyKeyboardRemove(),
        )


ALARM_CONVO_HANDLER = ConversationHandler(
    entry_points=[CommandHandler(HPJCommands.ALARM, AlarmHandlers.alarm)],
    states={
        ALARM_CONVO: [
            MessageHandler(filters.TEXT, AlarmHandlers.alarm_convo),
        ]
    },
    fallbacks=[],
    persistent=True,
    name="alarm_convo",
)


ALARM_CANCEL_HANDLER = CommandHandler(HPJCommands.CANCEL, AlarmHandlers.cancel)
