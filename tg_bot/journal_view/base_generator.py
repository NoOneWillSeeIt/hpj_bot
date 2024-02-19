from abc import ABC, abstractmethod


class IFileGenerator(ABC):
    """Base generator interface."""

    _extension: str = ''
    _name_prefix: str = 'hpj'

    @abstractmethod
    async def generate_async(self, questions: dict, replies: dict) -> bytes:
        ...

    @abstractmethod
    def generate(self, questions: dict, replies: dict) -> bytes:
        ...

    @property
    def extension(self) -> str:
        return self._extension

    def gen_filename(self, name: str) -> str:
        return f'{self._name_prefix}_{name}.{self.extension}'
