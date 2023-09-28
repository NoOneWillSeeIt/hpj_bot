from datetime import datetime, timedelta
from typing import Callable, List, Optional, Self, Union


class QuestionBase:

    def __init__(self, 
                 text: str, 
                 next_q: Union[Callable[[Self, str], Self], Self, None] = None,
                 options: Union[List[str], Callable[..., List[str]]] = [],
                 strict_options: bool = True,
                 validators: Optional[List[Callable[[Self, str], bool]]] = []) -> None:
        self._text = text
        self._next_q = next_q
        self._options = options or []
        self._strict_options = strict_options
        self._validators = validators or []
        self._note = ''

    @property
    def note(self) -> str:
        if not self._note and self._options and self._strict_options:
            return '\nВыбери ответ из списка'
        return self._note

    @note.setter
    def note(self, note: str) -> None:
        self._note = note

    @property
    def text(self) -> str:
        return self._text + self.note

    def __str__(self) -> str:
        return self.text

    @property
    def options(self) -> List[str]:
        if callable(self._options):
            return self._options()
        return self._options

    def _validate_reply_options(self, answer) -> bool:
        if not (self.options and self._strict_options):
            return True
        
        if answer.lower() in [pa.lower() for pa in self.options]:
            return True

        self.note = '\nОтветом являются только варианты: ' + ', '.join(self.options)
        return False

    def reply(self, answer: str) -> Optional[Self]:
        if not self._validate_reply_options(answer):
            return self

        for validator in self._validators:
            if not validator(self, answer):
                return self
        
        return self._next_q(self, answer) if callable(self._next_q) else self._next_q
