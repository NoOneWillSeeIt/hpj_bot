from datetime import datetime

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from commands import HPJCommands
from constants import ALARM_JOB_PREFIX, MSK_TIMEZONE_OFFSET
import db.aio_queries as asyncdb
from jobs import reminder


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
                'Нужно указать время по московскому часовому поясу в виде чч:мм.')
            return ALARM_CONVO

        return ConversationHandler.END

    @classmethod
    async def alarm_convo(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Alarm conversation. Conversation ends in any case."""
        if not await cls._set_alarm(update, context):
            await update.message.reply_text(
                f'Неверный формат, попробуй ещё раз нажать /{HPJCommands.ALARM}')

        return ConversationHandler.END

    @classmethod
    async def _set_alarm(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Sets alarm if update.message contains valid time and return True.
        Return False otherwise."""
        try:
            chat_id = update.message.chat_id
            user_input = update.message.text.strip()
            if context.args:
                user_input = context.args[0]

            time = datetime.strptime(user_input, '%H:%M').time()
            time = time.replace(tzinfo=MSK_TIMEZONE_OFFSET)

            job_name = f'{ALARM_JOB_PREFIX}{chat_id}'
            remove_job_if_exists(job_name, context)

            context.job_queue.run_daily(reminder, time, name=job_name, chat_id=chat_id)

            await asyncdb.write_alarm(context.bot_data, chat_id, time)

            await update.message.reply_text(
                f'Оповещения будут приходить в {time.strftime("%H:%M")}')
        except (ValueError, IndexError):
            return False

        return True

    @classmethod
    async def cancel(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Drop alarm time from table."""
        chat_id = update.message.chat_id
        remove_job_if_exists(f'{ALARM_JOB_PREFIX}{chat_id}', context)
        await asyncdb.clear_alarm(context.bot_data, chat_id)
        await update.message.reply_text(
            'Больше уведомлений не будет. Спасибо за использование, выздоравливай!',
            reply_markup=ReplyKeyboardRemove()
        )


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove job from queue."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return
    for job in current_jobs:
        job.schedule_removal()


ALARM_CONVO_HANDLER = ConversationHandler(
    entry_points=[CommandHandler(HPJCommands.ALARM, AlarmHandlers.alarm)],
    states={
        ALARM_CONVO: [
            MessageHandler(filters.TEXT, AlarmHandlers.alarm_convo),
        ]
    },
    fallbacks=[],
    persistent=True,
    name='alarm_convo',
)


ALARM_CANCEL_HANDLER = CommandHandler(HPJCommands.CANCEL, AlarmHandlers.cancel)
