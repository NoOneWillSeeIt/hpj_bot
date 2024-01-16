from abc import ABC
from typing import Callable, Final, List, Optional, Self, Tuple


class IQuestion(ABC):
    """Interface that represents questions"""

    SAME: Final[int] = -1
    END: Final[int] = -2

    @property
    def text(self) -> str:
        return ''

    @property
    def options(self) -> List[str]:
        return []

    def reply(self, answer: str) -> Optional[Self]:
        return None


class BaseQuestion(IQuestion):
    """Simple question which can take answer and return next question"""

    def __init__(self,
                 text: str,
                 next_q: Callable[[str], object] | object) -> None:
        self._text = text
        self._next_q = next_q

    def __str__(self) -> str:
        return self.text

    @property
    def text(self) -> str:
        return str(self._text)

    def reply(self, answer: str) -> object:
        return self._next_q(answer) if callable(self._next_q) else self._next_q


class OptionQuestion(BaseQuestion):
    """Question with non strict suggestions"""

    def __init__(self,
                 text: str,
                 next_q: Callable[[str], object] | object,
                 options: List[str]) -> None:
        super().__init__(text, next_q)
        self._options = options
        self._note = ''

    @property
    def text(self) -> str:
        if self._note:
            return self._text + '\n' + self._note
        return self._text

    @property
    def options(self) -> List[str]:
        if callable(self._options):
            return self._options()
        return self._options


class StrictOptionQuestion(OptionQuestion):
    """Question with strict where only given options can be used as an answer"""

    def reply(self, answer: str) -> Self | None:
        if answer.lower() not in [opt.lower() for opt in self.options]:
            self._note = 'Ответом являются только варианты: ' + ', '.join(self.options)
            return self.SAME

        return super().reply(answer)


class CustomValidatedQuestion(OptionQuestion):
    """Question with custom validations on answer.
    Inherited from OptionQuestion so any given option is not strict.
    """

    def __init__(self,
                 text: str,
                 next_q: Callable[[str], object] | object,
                 options: List[str]) -> None:
        super().__init__(text, next_q, options)
        self._validations = []

    def add_validation(self, validation: Callable[[str], bool], err_msg: str | None = None):
        self._validations.append((validation, err_msg))

    def reply(self, answer: str) -> str | None:
        for validation, err_msg in self._validations:
            if not validation(answer):
                self._note = err_msg
                return self.SAME

        return super().reply(answer)


def create_question(
    text: str,
    next_q: Callable[[str], object] | object,
    options: List[str] = [],
    strict_options: bool = True,
    validations: List[Tuple[Callable[[str], bool], str]] = [],
) -> IQuestion:
    """Factory method which creates questions with IQuestion interface.

    Args:
        text (str): Question text.
        next_q (Callable[[str], object] | object): Next question after replying.
        options (List[str], optional): Reply options. Defaults to [].
        strict_options (bool, optional): Is reply options strict. Defaults to True.
        validations (List[Tuple[Callable[[str], bool], str]], optional): Custom validations for
        question to add. Defaults to [].

    Returns:
        IQuestion: Question with provided attributes.
    """

    if validations:
        question = CustomValidatedQuestion(text, next_q, options)
        for validation, err_msg in validations:
            question.add_validation(validation, err_msg)
    elif strict_options and options:
        question = StrictOptionQuestion(text, next_q, options)
    elif options:
        question = OptionQuestion(text, next_q, options)
    else:
        question = BaseQuestion(text, next_q)

    return question
