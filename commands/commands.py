from enum import StrEnum, auto


class HPJCommands(StrEnum):
    START = auto()
    HELP = auto()
    ALARM = auto()
    ADD_ENTRY = 'add'
    LOAD = auto()
    CANCEL = auto()
    CLEAR = auto()  # TODO: give an option to delete user data
    RESTART = auto()
    BACK = auto()
    STOP = auto()


default_command_description = {
    HPJCommands.START: 'Сказать привет',
    HPJCommands.HELP: 'Справка по командам',
    HPJCommands.ALARM: 'Установить напоминание',
    HPJCommands.ADD_ENTRY: 'Добавить новую запись в журнал',
    HPJCommands.LOAD: 'Выгрузить дневник',
    HPJCommands.CANCEL: 'Отменить подписку на уведы',
    HPJCommands.CLEAR: 'Стереть все свои данные',
    HPJCommands.RESTART: 'Начать заново',
    HPJCommands.BACK: 'Вернуться к предыдущему вопросу',
    HPJCommands.STOP: 'Перестать заполнять',
}
