from typing import List

from telegram import BotCommandScopeChat, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import BaseHandler, CommandHandler, ContextTypes, ConversationHandler, \
    MessageHandler, filters

import db_queries as db
from commands import HPJCommands
from hpj_questions import get_head_pain_survey, prepare_answers_for_db
from menu_commands import DefaultMenuCommands, SurveyMenuCommands
from survey import Survey


SURVEY_CONVO = 0


class SurveyHandlers:

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
            await context.bot.set_my_commands(DefaultMenuCommands().menu, 
                                              BotCommandScopeChat(update.message.chat_id))
            
            await db.write_entry(context.bot_data, update.message.chat_id, 
                                 prepare_answers_for_db(survey.replies))
            
            await update.message.reply_text('Сохранено. Выздоравливай!', 
                                            reply_markup=ReplyKeyboardRemove())
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
        
        await context.bot.set_my_commands(DefaultMenuCommands().menu, 
                                          BotCommandScopeChat(update.message.chat_id))

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

        await SurveyHandlers.convo(update, context)
    

def get_survey_keyboard(survey: Survey):
    if survey and survey.isongoing and survey.question.options:
        keyboard = [[ans for ans in survey.question.options]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    return ReplyKeyboardRemove()


def get_handlers() -> List[BaseHandler]:
    return [
        ConversationHandler(
            entry_points=[CommandHandler(HPJCommands.ADD_ENTRY, SurveyHandlers.convo)],
            states={
                SURVEY_CONVO: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, SurveyHandlers.convo), 
                    CommandHandler(HPJCommands.BACK, SurveyHandlers.back),
                    CommandHandler(HPJCommands.RESTART, SurveyHandlers.restart),
                ],
            },
            fallbacks=[CommandHandler(HPJCommands.STOP, SurveyHandlers.stop)],
        )
    ]