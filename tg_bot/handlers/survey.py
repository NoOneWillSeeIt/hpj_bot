import logging
from datetime import timedelta

from telegram import (
    BotCommandScopeChat,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from common.survey.hpj_questions import get_head_pain_survey
from common.survey.survey import Survey
from tg_bot.commands import HPJCommands, SurveyMenuCommands
from tg_bot.requests import is_new_user, save_report

SURVEY_CONVO = 0


class SurveyHandlers:
    """Survey conversation handlers"""

    @classmethod
    async def start(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Starts survey and greets user if it's first time."""
        chat_id = update.message.chat_id
        err, is_new = await is_new_user(chat_id)
        if err:
            await update.message.reply_text("Что-то пошло не так. Попробуй позже.")
            return ConversationHandler.END

        if is_new:
            await update.message.reply_text(
                "Опрос можно перезапустить, вернуться к предыдущему вопросу или остановить, чтобы "
                "вернуться позже. Для управления опросом пользуйся меню команд\n↓"
            )

        job_name = f"survey_reminder_{chat_id}"
        context.job_queue.run_once(
            survey_reminder, timedelta(hours=2), name=job_name, chat_id=chat_id
        )
        return await SurveyHandlers.convo(update, context)

    @classmethod
    async def convo(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Survey conversation handler - asks questions until survey exhaust or user sends
        stop command."""

        survey: Survey | None = context.chat_data.get("survey")

        if survey:
            survey.reply(update.message.text or "")
        else:
            await context.bot.set_my_commands(
                SurveyMenuCommands().menu, BotCommandScopeChat(update.message.chat_id)
            )
            survey = get_head_pain_survey()
            context.chat_data["survey"] = survey

        if survey.isongoing:
            await update.message.reply_text(
                survey.question.text, reply_markup=get_survey_keyboard(survey)
            )

            return SURVEY_CONVO

        chat_id = update.message.chat_id
        await context.bot.delete_my_commands(BotCommandScopeChat(chat_id))
        msg = "Сохранено. Выздоравливай!"
        err = await save_report(chat_id, survey.replies)
        if err:
            msg = "Не удалось сохранить. Попробуй позже."
            await context.application.process_error(update, err)

        await update.message.reply_text(msg, reply_markup=get_survey_keyboard(survey))
        del context.chat_data["survey"]
        return ConversationHandler.END

    @classmethod
    async def stop(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Interrupt survey."""
        survey = context.chat_data["survey"]
        if survey:
            survey.stop()
            del context.chat_data["survey"]

        await context.bot.delete_my_commands(
            BotCommandScopeChat(update.message.chat_id)
        )

        await update.message.reply_text(
            "Приходи заполнять журнал, когда будет удобно!",
            reply_markup=get_survey_keyboard(survey),
        )

        return ConversationHandler.END

    @classmethod
    async def back(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Go to previous question."""
        survey: Survey = context.chat_data["survey"]
        survey.go_back()
        await update.message.reply_text(
            survey.question.text, reply_markup=get_survey_keyboard(survey)
        )

        return SURVEY_CONVO

    @classmethod
    async def restart(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Restart survey from the beginning."""
        survey = context.chat_data["survey"]
        if survey:
            del context.chat_data["survey"]

        return await SurveyHandlers.convo(update, context)


def get_survey_keyboard(
    survey: Survey | None,
) -> ReplyKeyboardMarkup | ReplyKeyboardRemove:
    """Returns survey keyboard based on question options."""
    if survey and survey.isongoing and survey.question.options:
        return ReplyKeyboardMarkup(
            [survey.question.options], resize_keyboard=True, one_time_keyboard=True
        )

    return ReplyKeyboardRemove()


async def survey_reminder(context: ContextTypes.DEFAULT_TYPE):
    survey: Survey | None = context.chat_data.get("survey")
    if survey and survey.isongoing:
        await context.bot.send_message(
            chat_id=context.job.chat_id, text="Кажется про меня забыли..."
        )


def remove_job_if_exists(context: ContextTypes.DEFAULT_TYPE, job_name: str):
    jobs = context.job_queue.get_jobs_by_name(job_name)
    if not jobs:
        return
    for job in jobs:
        job.schedule_removal()


SURVEY_CONVO_HANDLER = ConversationHandler(
    entry_points=[CommandHandler(HPJCommands.ADD_ENTRY, SurveyHandlers.start)],
    states={
        SURVEY_CONVO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, SurveyHandlers.convo),
            CommandHandler(HPJCommands.BACK, SurveyHandlers.back),
            CommandHandler(HPJCommands.RESTART, SurveyHandlers.restart),
        ],
    },
    fallbacks=[CommandHandler(HPJCommands.STOP, SurveyHandlers.stop)],
    persistent=True,
    name="survey_convo",
)
