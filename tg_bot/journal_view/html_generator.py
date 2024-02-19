from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from tg_bot.journal_view.base_generator import IFileGenerator


class HTMLGenerator(IFileGenerator):
    """HTML report generator."""

    _extension = 'html'

    def __init__(self, folder_path: str | Path, template_name: str,
                 enable_async: bool = True) -> None:
        """Init HTML generator.

        Args:
            folder_path (str | Path): Path to folder with templates.
            template_name (str): Template file name.
            enable_async (bool, optional): Enables async generator mode. Defaults to True.
        """
        self._env = Environment(loader=FileSystemLoader(folder_path, encoding='utf-8'),
                                enable_async=enable_async)
        self._template = self._env.get_template(template_name)

    @property
    def template(self) -> Template:
        """Returns current jinja2.Template."""
        return self._template

    def _prepare_render_params(self, questions: dict, replies: dict):
        """Prepares data for template."""
        replies_keys = sorted(replies.keys(), key=lambda x: datetime.strptime(x, '%d.%m'))
        params = {
            'start_date': replies_keys[0],
            'end_date': replies_keys[-1],
            'replies_list': [questions] + [replies[key] for key in replies_keys],
            'question_list': list(questions.keys()),
        }

        return params

    async def generate_async(self, questions: dict, replies: dict) -> bytes:
        """Async file generation.

        Args:
            questions (dict): Dict of questions.
            replies (dict): Dict of replies from surveys.

        Raises:
            RuntimeError: raises when generator was created with enable_async=False.

        Returns:
            bytes: Generated file.
        """
        if not self._env.is_async:
            raise RuntimeError('Generator was not created async')

        str_file = await self.template.render_async(
            **self._prepare_render_params(questions, replies)
        )
        return str_file.encode(encoding='utf-8')

    def generate(self, questions: dict, replies: dict) -> bytes:
        """File generation.

        Args:
            questions (dict): Dict of questions.
            replies (dict): Dict of replies from surveys.

        Raises:
            RuntimeError: raises when generator was created with enable_async=True.

        Returns:
            bytes: Generated file.
        """
        if self._env.is_async:
            raise RuntimeError('Generator was created async')

        str_file = self.template.render(
            **self._prepare_render_params(questions, replies)
        )
        return str_file.encode(encoding='utf-8')
