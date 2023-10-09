from enum import StrEnum, auto


class HPJCommands(StrEnum):
    START = auto()
    HELP = auto()  # currently unused
    ALARM = auto()
    ADD_ENTRY = 'add'
    CANCEL = auto()
    RESTART = auto()
    BACK = auto()
    STOP = auto()


default_command_description = {
    HPJCommands.START: 'Сказать привет',
    HPJCommands.ALARM: 'Установить напоминание',
    HPJCommands.ADD_ENTRY: 'Добавить новую запись в журнал',
    HPJCommands.CANCEL: 'Отменить подписку на уведы',
    HPJCommands.RESTART: 'Начать заново',
    HPJCommands.BACK: 'Вернуться к предыдущему вопросу',
    HPJCommands.STOP: 'Перестать заполнять',
}
