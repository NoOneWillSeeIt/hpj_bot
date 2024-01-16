from survey.question_base import IQuestion


class Survey:
    """Survey class for navigating through questions."""

    def __init__(self, questions: dict[object, IQuestion], initial_question_key: str) -> None:
        """Init survey.

        Args:
            questions (dict[object, IQuestion]): Dictionary of questions to navigate.
            initial_question_key (str): Initial question to start from.
        """
        self._questions = questions
        self._question_stack = []
        self._replies = {}
        self._question_key = initial_question_key

    @property
    def question(self):
        """Returns current question."""
        return self._questions.get(self._question_key)

    @question.setter
    def question(self, question: object):
        """Sets the new current question.
        If question == IQuestion.SAME does nothing.
        If question == IQuestion.END sets current question to None.

        Args:
            question (object): Next question key from questions dict.
        """
        if question == IQuestion.SAME:
            return

        if question == IQuestion.END:
            self._question_key = None
            return

        if self._question_key != question:
            self._question_stack.append(self._question_key)
        self._question_key = question

    def reply(self, answer: str) -> None:
        """Validate reply and set new question."""
        answer = answer.strip()
        self._replies[self._question_key] = answer
        self.question = self.question.reply(answer)

    @property
    def replies(self):
        """Returns all replies."""
        return self._replies.copy()

    def go_back(self):
        """Returns to previous question."""
        try:
            self._question_key = self._question_stack.pop()
        except IndexError:
            ...

    def stop(self):
        """Interrupts survey."""
        self._question_key = None

    @property
    def isongoing(self) -> bool:
        """Returns is sruvey still in progress or not."""
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
