from enum import Enum, auto
from typing import Final
from survey.question_base import IQuestion


class Survey:

    def __init__(self, questions: dict[object, IQuestion], initial_question_key: str) -> None:
        self._questions = questions
        self._question_stack = []
        self._replies = {}
        self._question_key = initial_question_key
    
    @property
    def question(self):
        return self._questions.get(self._question_key)

    @question.setter
    def question(self, question: object):
        if question == IQuestion.SAME:
            return
        
        if question == IQuestion.END:
            self._question_key = None
            return
        
        if self._question_key != question:
            self._question_stack.append(self._question_key)
        self._question_key = question

    def reply(self, answer: str) -> None:
        answer = answer.strip()
        self._replies[self._question_key] = answer
        self.question = self.question.reply(answer)

    @property
    def replies(self):
        return self._replies.copy()

    def go_back(self):
        try:
            self._question_key = self._question_stack.pop()
        except IndexError:
            ...

    def stop(self):
        self._question_key = None
    
    @property
    def isongoing(self) -> bool:
        return self.question is not None

'''
Пример прохождения опроса:

def main_loop():
    survey = Survey(questions, init_question)
    while survey.isongoing:
        print(survey.question)
        if survey.question.options:
            print(survey.question.options)
        
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
