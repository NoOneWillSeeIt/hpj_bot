__all__ = (
    'all_handlers'
)

from .alarm import get_handlers as alarm_handlers
from .info import get_handlers as info_handlers
from .survey import get_handlers as survey_handlers


all_handlers = [
    *alarm_handlers(),
    *info_handlers(),
    *survey_handlers(),
]
