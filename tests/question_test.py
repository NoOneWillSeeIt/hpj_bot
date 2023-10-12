import unittest

from survey.question_base import BaseQuestion, CustomValidatedQuestion, IQuestion, OptionQuestion, \
    StrictOptionQuestion, create_question


class TestQuestion(unittest.TestCase):

    def test_question_creation(self):
        question = create_question('1', '2')
        self.assertTrue(isinstance(question, BaseQuestion))

        question = create_question('1', '2', options=['1', '2'])
        self.assertTrue(isinstance(question, StrictOptionQuestion))

        question = create_question('1', '2', options=['1', '2'], strict_options=False)
        self.assertTrue(isinstance(question, OptionQuestion))

        question = create_question('1', '2', options=['1', '2'], validations=[(lambda x: x, 'msg')])
        self.assertTrue(isinstance(question, CustomValidatedQuestion))

        question = create_question('1', '2', options=['1', '2'], strict_options=False,
                                   validations=[(lambda x: x, 'msg')])
        self.assertTrue(isinstance(question, CustomValidatedQuestion))

    def test_base_question(self):
        sample_text = 'text'
        next_question = '2'
        question = BaseQuestion(sample_text, next_question)

        self.assertEqual(question.text, sample_text)
        self.assertEqual(question.reply('1'), next_question)

    def test_option_question(self):
        sample_text = 'text'
        next_question = '2'
        options = ['yes', 'no']
        question = OptionQuestion(sample_text, next_question, options)

        self.assertEqual(question.text, sample_text)
        self.assertEqual(question.options, options)
        self.assertEqual(question.reply('1'), next_question)

    def test_strict_option_question(self):
        sample_text = 'text'
        next_question = '2'
        options = ['yes', 'no']
        question = StrictOptionQuestion(sample_text, next_question, options)

        self.assertEqual(question.text, sample_text)
        self.assertEqual(question.options, options)
        self.assertEqual(question.reply('1'), IQuestion.SAME)
        self.assertEqual(question.reply(options[0]), next_question)

    def test_custom_validated_question(self):
        sample_text = 'text'
        next_question = '2'
        options = ['yes', 'no']
        err_msg = 'err_text'
        question = CustomValidatedQuestion(sample_text, next_question, options)
        question.add_validation(lambda x: x == options[0], err_msg)

        self.assertEqual(question.text, sample_text)
        self.assertEqual(question.options, options)
        self.assertEqual(question.reply('1'), IQuestion.SAME)
        self.assertEqual(question._note, err_msg)
        self.assertEqual(question.reply(options[0]), next_question)
