from telegram import BotCommandScopeChat, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import db.aio_queries as asyncdb
from commands import HPJCommands, SurveyMenuCommands
from hpj_questions import get_head_pain_survey, prepare_answers_for_db
from survey import Survey


SURVEY_CONVO = 0


class SurveyHandlers:

    @classmethod
    async def start(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await asyncdb.is_new_user(context.bot_data, update.message.chat_id):
            await update.message.reply_text(
                'Опрос можно перезапустить, вернуться к предыдущему вопросу или остановить, чтобы '
                'вернуться позже. Для управления опросом пользуйся меню команд\n↓'
            )
        return await SurveyHandlers.convo(update, context)

    @classmethod
    async def convo(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        survey = context.chat_data.get('survey')

        if not survey:
            await context.bot.set_my_commands(SurveyMenuCommands().menu,
                                              BotCommandScopeChat(update.message.chat_id))
            survey = get_head_pain_survey()
            context.chat_data['survey'] = survey

        else:
            survey.reply(update.message.text)

        if not survey.isongoing:
            chat_id = update.message.chat_id
            await context.bot.delete_my_commands(BotCommandScopeChat(chat_id))

            await asyncdb.write_entry(context.bot_data, chat_id,
                                      *prepare_answers_for_db(survey.replies))

            await update.message.reply_text('Сохранено. Выздоравливай!',
                                            reply_markup=get_survey_keyboard(survey))
            del context.chat_data['survey']
            return ConversationHandler.END

        await update.message.reply_text(
            survey.question.text, reply_markup=get_survey_keyboard(survey))

        return SURVEY_CONVO

    @classmethod
    async def stop(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        survey = context.chat_data['survey']
        if survey:
            survey.stop()
            del context.chat_data['survey']

        await context.bot.delete_my_commands(BotCommandScopeChat(update.message.chat_id))

        await update.message.reply_text('Приходи заполнять журнал, когда будет удобно!',
                                        reply_markup=get_survey_keyboard(survey))

        return ConversationHandler.END

    @classmethod
    async def back(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        survey = context.chat_data.get('survey')
        survey.go_back()
        await update.message.reply_text(
            survey.question.text, reply_markup=get_survey_keyboard(survey))

        return SURVEY_CONVO

    @classmethod
    async def restart(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        survey = context.chat_data['survey']
        if survey:
            del context.chat_data['survey']

        return await SurveyHandlers.convo(update, context)


def get_survey_keyboard(survey: Survey):
    if survey and survey.isongoing and survey.question.options:
        return ReplyKeyboardMarkup(
            [survey.question.options], resize_keyboard=True, one_time_keyboard=True
        )

    return ReplyKeyboardRemove()


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
    name='survey_convo',
)
