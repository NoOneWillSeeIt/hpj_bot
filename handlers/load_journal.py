from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from commands import HPJCommands
from constants import FLASK_PIC_PATH, OutputFileFormats
import db.aio_queries as asyncdb
from hpj_questions import Questions


class LoadJournalHandlers:
    """Handlers for loading full journal."""

    @classmethod
    async def load(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /load command and suggests file formats."""
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
        """Handles file format choosing. Generates report and send it to user."""
        query = update.callback_query
        chat_id = query.message.chat_id

        generator = context.bot_data['file_generators'][query.data]
        entries = await asyncdb.read_entries(context.bot_data, chat_id)
        await query.answer()
        if not entries:
            await query.edit_message_text('У меня нет твоих записей ¯\\_(ツ)_/¯', reply_markup=None)
            return

        out_file_bytes = await generator.generate_async(Questions.to_dict(), entries)
        filename = generator.gen_filename(str(chat_id))

        await query.edit_message_text('Вот те записи, что у меня есть:', reply_markup=None)
        await context.bot.send_document(chat_id, document=out_file_bytes,
                                        filename=filename, thumbnail=FLASK_PIC_PATH)


LOAD_HANDLER = CommandHandler(HPJCommands.LOAD, LoadJournalHandlers.load)


LOAD_CALLBACK_HANDLER = CallbackQueryHandler(
    LoadJournalHandlers.load_choose,
    pattern='^' + '|'.join(ext.value for ext in OutputFileFormats) + '$'
)
