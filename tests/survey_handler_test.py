from unittest.mock import AsyncMock

from telegram import KeyboardButton, ReplyKeyboardRemove

from commands import HPJCommands
from commands.menu_commands import SurveyMenuCommands
from handlers.survey import SURVEY_CONVO_HANDLER
from tests.utils.ptb_app import TEST_CHAT_ID, make_command, make_update, send_command, send_message
from tests.utils.test_cases import AsyncTelegramBotTestCase


class SurveyHandlerTest(AsyncTelegramBotTestCase):

    _handlers = [SURVEY_CONVO_HANDLER]

    def _check_convo_ready_to_start(self):
        new_update = make_update(self.app.bot, make_command(self.app.bot,
                                                            f'/{HPJCommands.ADD_ENTRY}'))
        return bool(SURVEY_CONVO_HANDLER.check_update(new_update))

    async def test_survey_start(self):
        set_cmd_mock = AsyncMock(wraps=self.app.bot.set_my_commands)
        self.app.bot.set_my_commands = set_cmd_mock

        send_mock = AsyncMock(wraps=self.app.bot.send_message)
        self.app.bot.send_message = send_mock

        await send_command(self.app, f'/{HPJCommands.ADD_ENTRY}')
        survey = self.app.chat_data[TEST_CHAT_ID]['survey']

        self.assertIsNotNone(survey)
        self.assertTrue(survey.isongoing)
        self.assertEqual(survey.question.text, send_mock.await_args.kwargs['text'])
        self.assertEqual(tuple(KeyboardButton(opt) for opt in survey.question.options),
                         send_mock.await_args.kwargs['reply_markup'].keyboard[0])
        set_cmd_mock.assert_awaited_once()
        self.assertEqual(
            set_cmd_mock.await_args.args[1].chat_id,
            TEST_CHAT_ID
        )
        self.assertEqual(
            set_cmd_mock.await_args.args[0],
            SurveyMenuCommands().menu
        )
        self.assertFalse(self._check_convo_ready_to_start())

    async def test_survey_back(self):
        await send_command(self.app, f'/{HPJCommands.ADD_ENTRY}')
        survey = self.app.chat_data[TEST_CHAT_ID]['survey']
        prev_question = survey.question.text
        await send_message(self.app,
                           survey.question.options[-1] if survey.question.options else '1')

        self.assertNotEqual(prev_question.lower(), survey.question.text.lower())

        for msg in ['first iteration', 'second iteration']:
            await send_command(self.app, f'/{HPJCommands.BACK}')
            self.assertTrue(survey.isongoing, msg)
            self.assertEqual(prev_question.lower(), survey.question.text.lower(), msg)
            self.assertFalse(self._check_convo_ready_to_start(), msg)

    async def test_survey_restart(self):
        await send_command(self.app, f'/{HPJCommands.ADD_ENTRY}')
        survey = self.app.chat_data[TEST_CHAT_ID]['survey']
        first_question = survey.question.text
        await send_message(
            self.app,
            survey.question.options[-1] if survey.question.options else '1'
        )

        self.assertNotEqual(first_question.lower(), survey.question.text.lower())

        await send_command(self.app, f'/{HPJCommands.RESTART}')
        survey = self.app.chat_data[TEST_CHAT_ID]['survey']

        self.assertTrue(survey.isongoing)
        self.assertEqual(first_question.lower(), survey.question.text.lower())
        self.assertFalse(self._check_convo_ready_to_start())

    async def test_survey_stop(self):
        del_cmd_mock = AsyncMock(wraps=self.app.bot.delete_my_commands)
        self.app.bot.delete_my_commands = del_cmd_mock

        send_mock = AsyncMock(wraps=self.app.bot.send_message)
        self.app.bot.send_message = send_mock

        await send_command(self.app, f'/{HPJCommands.ADD_ENTRY}')
        await send_command(self.app, f'/{HPJCommands.STOP}')

        self.assertNotIn('survey', self.app.chat_data[TEST_CHAT_ID])
        self.assertTrue(
            isinstance(send_mock.await_args.kwargs['reply_markup'],
                       ReplyKeyboardRemove)
        )
        self.assertEqual(
            del_cmd_mock.await_args.args[0].chat_id,
            TEST_CHAT_ID
        )
        self.assertTrue(self._check_convo_ready_to_start())
