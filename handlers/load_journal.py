from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import BaseHandler, CommandHandler, ContextTypes, CallbackQueryHandler

from commands.commands import HPJCommands
from constants import FLASK_PIC_PATH, OutputFileFormats
import db.aio_queries as db
from hpj_questions import Questions


class LoadJournalHandlers:

    @classmethod
    async def load(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [
                InlineKeyboardButton(file_format.name, callback_data=file_format.value)
                for file_format in OutputFileFormats
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text('Выбери формат:', reply_markup=reply_markup)

    @classmethod
    async def load_choose(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        chat_id = query.message.chat_id

        generator = context.bot_data['file_generators'][query.data]
        entries = await db.read_entries(context.bot_data, chat_id)
        if not entries:
            await query.edit_message_text('У меня нет твоих записей ¯\\_(ツ)_/¯', reply_markup=None)
            return

        out_file_bytes = await generator.generate_file(Questions.to_dict(), entries)
        filename = generator.gen_filename(str(chat_id))

        await query.answer()
        await query.edit_message_text('Вот те записи, что у меня есть:', reply_markup=None)
        await context.bot.send_document(chat_id, document=out_file_bytes,
                                        filename=filename, thumbnail=FLASK_PIC_PATH)


def get_handlers() -> List[BaseHandler]:
    load_handler = CommandHandler(HPJCommands.LOAD, LoadJournalHandlers.load)
    file_formats_patterns = '^' + '|'.join(ext.value for ext in OutputFileFormats) + '$'
    load_callback_handler = CallbackQueryHandler(LoadJournalHandlers.load_choose,
                                                 pattern=file_formats_patterns)
    return [load_handler, load_callback_handler]
