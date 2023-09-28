from datetime import datetime, timezone, timedelta
import os

from telegram import BotCommandScopeChat, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters


import db_manager
from hpj_questions import get_head_pain_survey
from survey import Survey


DEFAULT_BUTTON_COMMANDS = [
    ('/start', 'Сказать привет'),
    ('/alarm', 'Установить напоминание'),
    ('/add', 'Добавить новую запись в журнал'),
    ('/cancel', 'Отменить подписку на уведы'),
]

SURVEY_MENU_COMMANDS = [
    ('/restart', 'Начать заново'),
    ('/back', 'Вернуться к предыдущему вопросу'),
    ('/stop', 'Перестать заполнять'),
]

MSK_TIMEZONE_OFFSET = timezone(timedelta(hours=3))

SURVEY_JOB_PREFIX = 'survey'
JOURNAL_JOB_PREFIX = 'journal'

SURVEY_CONVO = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я буду вести дневник твоих головных болей.\n'\
                                    'Заполнять его нужно перед сном. Чтобы не забывать можешь '\
                                    'поставить напоминание через команду /alarm чч:мм')


async def survey_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    survey = context.chat_data['survey']
    if survey:
        del context.chat_data['survey']
    
    await context.bot.set_my_commands(DEFAULT_BUTTON_COMMANDS, 
                                      BotCommandScopeChat(update.message.chat_id))
    await update.message.reply_text(
        'Приходи заполнять журнал, когда будет удобно!', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def build_survey_keyboard(survey: Survey):
    if survey.question_options:
        keyboard = [[ans for ans in survey.question_options]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, 
                                       one_time_keyboard=True)

    return None


async def survey_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    survey = context.chat_data.get('survey')
    survey.go_back()
    await update.message.reply_text(
        survey.question.text, reply_markup=build_survey_keyboard(survey))

    return SURVEY_CONVO


async def survey_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    survey = context.chat_data['survey']
    if survey:
        del context.chat_data['survey']

    await survey_convo(update, context)


async def survey_convo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    survey = context.chat_data.get('survey')
    answer = update.message.text

    if not survey:
        await context.bot.set_my_commands(SURVEY_MENU_COMMANDS, 
                                          BotCommandScopeChat(update.message.chat_id))
        survey = get_head_pain_survey()
        context.chat_data['survey'] = survey

    else:
        survey.reply(answer)

    if not survey.has_questions():
        await context.bot.set_my_commands(DEFAULT_BUTTON_COMMANDS, 
                                          BotCommandScopeChat(update.message.chat_id))
        
        await db_manager.db_write_entry(context.bot_data, update.message.chat_id, survey.replies)
        
        await update.message.reply_text('Сохранено. Выздоравливай!', 
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    await update.message.reply_text(
        survey.question.text, reply_markup=build_survey_keyboard(survey))

    return SURVEY_CONVO


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return
    for job in current_jobs:
        job.schedule_removal()


async def reminder(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=context.job.chat_id, 
                                   text='Привет, нужно заполнить журнал. Напиши /add и вперёд!')


async def alarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    try:
        time = datetime.strptime(context.args[0], '%H:%M').time()
        time = time.replace(tzinfo=MSK_TIMEZONE_OFFSET)

        job_name = f'{SURVEY_JOB_PREFIX}{chat_id}'
        remove_job_if_exists(job_name, context)

        context.job_queue.run_daily(reminder, time, name=job_name, chat_id=chat_id)

        await db_manager.db_write_alarm(context.bot_data, chat_id, time)

        await update.message.reply_text(f'Оповещения будут приходить в {time.strftime("%H:%M")}')

    except (ValueError, IndexError):
        await update.message.reply_text(
            'Нужно указать время по московскому часовому поясу в виде чч:мм. '\
            'Пример команды: \n/alarm 23:55')


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    remove_job_if_exists(f'{SURVEY_JOB_PREFIX}{chat_id}', context)
    await update.message.reply_text(
        'Больше уведомлений не будет. Спасибо за использование, выздоравливай!', 
        reply_markup=ReplyKeyboardRemove()
    )


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(DEFAULT_BUTTON_COMMANDS)


def configure_app() -> Application:
    application = ApplicationBuilder().token(os.environ.get('HPJ_TOKEN')).post_init(post_init).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    
    alarm_handler = CommandHandler('alarm', alarm)
    application.add_handler(alarm_handler)

    cancel_handler = CommandHandler('cancel', cancel)
    application.add_handler(cancel_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', survey_convo)],
        states={
            SURVEY_CONVO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, survey_convo), 
                CommandHandler('back', survey_back),
                CommandHandler('restart', survey_restart),
                ],
        },
        fallbacks=[CommandHandler('stop', survey_stop)],
    )
    application.add_handler(conv_handler)

    return application
