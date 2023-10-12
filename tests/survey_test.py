
import unittest

from survey import create_question, IQuestion, Survey


class TestSurvey(unittest.TestCase):

    def setUp(self) -> None:
        self.questions = {
             '1': create_question('sample text 1', next_q='2'),
             '2': create_question('sample text 2', next_q='3', options=['3']),
             '3': create_question('sample text 3', next_q=IQuestion.END),
        }
        self.survey = Survey(self.questions, '1')

    def test_reply(self):
        self.survey.reply('1')
        self.assertEqual(self.questions['2'], self.survey.question)

    def test_go_back(self):
        first_question = self.survey.question
        self.survey.reply('2')
        second_question = self.survey.question
        self.survey.reply('3')

        self.survey.go_back()
        self.assertEqual(self.survey.question, second_question)

        self.survey.go_back()
        self.assertEqual(self.survey.question, first_question)

        self.survey.go_back()
        self.assertEqual(self.survey.question, first_question,
                         msg='question must stay the same if go_back called on first question')

    def test_stop(self):
        self.survey.reply('1')
        self.survey.stop()

        self.assertIsNone(self.survey.question)
        self.assertFalse(self.survey.isongoing)

    def test_exhaust(self):
        self.survey.reply('1')
        self.survey.reply('3')
        self.survey.reply('3')

        self.assertFalse(self.survey.isongoing)
        self.assertIsNone(self.survey.question)

    def test_wrong_options(self):
        self.survey.reply('1')
        question = self.survey.question
        self.survey.reply('2')

        self.assertEqual(self.survey.question, question)
