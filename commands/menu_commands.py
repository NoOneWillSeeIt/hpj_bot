from telegram import BotCommand
from .commands import HPJCommands, default_command_description


class MenuCommands:

    command_list = []

    def __init__(self, command_description: dict[str, str] = default_command_description) -> None:
        self._command_description = command_description

    @property
    def menu(self):
        return [
            BotCommand(command, self._command_description[command])
            for command in self.command_list
        ]


class DefaultMenuCommands(MenuCommands):

    command_list = [HPJCommands.START, HPJCommands.HELP, HPJCommands.ALARM, HPJCommands.ADD_ENTRY,
                    HPJCommands.LOAD, HPJCommands.CANCEL]


class SurveyMenuCommands(MenuCommands):

    command_list = [HPJCommands.RESTART, HPJCommands.BACK, HPJCommands.STOP]
