__all__ = (
    'all_handlers',
    'error_handler'
)

from .alarm import get_handlers as alarm_handlers
from .error import error_handler
from .info import get_handlers as info_handlers
from .load_journal import get_handlers as load_handlers
from .survey import get_handlers as survey_handlers


all_handlers = [
    *alarm_handlers(),
    *info_handlers(),
    *load_handlers(),
    *survey_handlers(),
]
