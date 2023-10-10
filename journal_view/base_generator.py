from abc import ABC, abstractmethod


class IFileGenerator(ABC):

    _extension: str = ''
    _name_prefix: str = 'hpj'

    @abstractmethod
    async def generate_file(self, questions: dict, replies: dict) -> bytes:
        ...

    @property
    def extension(self) -> str:
        return self._extension

    def gen_filename(self, name: str) -> str:
        return f'{self._name_prefix}_{name}.{self.extension}'
