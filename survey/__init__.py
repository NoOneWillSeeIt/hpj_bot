"""
Module survey provides:

Survey class for navigation through questions and collecting answers;

IQuestion interface that represents questions;

create_question fabric method for creating questions.
"""

__all__ = (
    'IQuestion',
    'Survey',
    'create_question',
)

from .question_base import IQuestion, create_question
from .survey import Survey
