from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from common.constants import ENTRY_DATE_FORMAT

from .base_generator import IFileGenerator


class HTMLGenerator(IFileGenerator):
    """HTML report generator."""

    _extension = "html"

    def __init__(
        self, folder_path: str | Path, template_name: str, questions: dict[str, str]
    ) -> None:
        """Init HTML generator.

        Args:
            folder_path (str | Path): Path to folder with templates.
            template_name (str): Template file name.
        """
        self._env = Environment(loader=FileSystemLoader(folder_path, encoding="utf-8"))
        self._template = self._env.get_template(template_name)
        self._questions = questions

    def _prepare_render_params(self, replies: dict):
        """Prepares data for template."""
        replies_keys = sorted(
            replies.keys(), key=lambda x: datetime.strptime(x, ENTRY_DATE_FORMAT)
        )
        params = {
            "start_date": replies_keys[0],
            "end_date": replies_keys[-1],
            "replies_list": [self._questions] + [replies[key] for key in replies_keys],
            "question_list": list(self._questions.keys()),
        }

        return params

    def generate(self, replies: dict[str, str]) -> bytes:
        """File generation.

        Args:
            replies (dict): Dict of replies from surveys.

        Returns:
            bytes: Generated file.
        """

        str_file = self._template.render(**self._prepare_render_params(replies))
        return str_file.encode(encoding="utf-8")
