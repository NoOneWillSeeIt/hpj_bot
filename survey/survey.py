from enum import Enum, auto
from typing import Final
from survey.question_base import QuestionBase


class SurveyStatus(Enum):
    ONGOING = auto()
    ABORTED = auto()
    FINISHED = auto()


class Survey:

    ONGOING: Final = SurveyStatus.ONGOING
    ABORTED: Final = SurveyStatus.ABORTED
    FINISHED: Final = SurveyStatus.FINISHED

    def __init__(self, questions: dict[str, str], initial_question_key: str) -> None:
        self._questions = questions
        self._question_stack = []
        self._replies = {}
        self._question_key = initial_question_key
        self._status = self.ONGOING
    
    @property
    def question(self):
        return self._questions.get(self._question_key)

    @question.setter
    def question(self, question: QuestionBase):
        if self._question_key != question:
            self._question_stack.append(self._question_key)
        self._question_key = question

    @property
    def status(self) -> SurveyStatus:
        return self._status

    @property
    def question_options(self):
        return self.question.options

    def reply(self, answer: str) -> None:
        answer = answer.strip()
        self._replies[self._question_key] = answer
        self.question = self.question.reply(answer)
        if not self.question:
            self._status = self.FINISHED

    @property
    def replies(self):
        return self._replies.copy()

    def go_back(self):
        try:
            self._question_key = self._question_stack.pop()
        except IndexError:
            ...

    def stop(self):
        if self._status == self.ONGOING:
            self._question_key = None
            self._status = self.ABORTED
      
    def has_questions(self) -> bool:
        return self._status is self.ONGOING

'''
Пример прохождения опроса:

def main_loop():
    survey = Survey(questions, init_question, key)
    while survey.has_questions():
        print(survey.question)
        if survey.question_options:
            print(survey.question_options)
        
        val = input('answer = ')
        if val == '/back':
            survey.go_back()
            continue
        elif val == '/break':
            survey.stop()
        else:
            survey.reply(val)
    
if __name__ == '__main__':
    main_loop()
'''
