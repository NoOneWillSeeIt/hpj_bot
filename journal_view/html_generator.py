from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from .base_generator import IFileGenerator


class HTMLGenerator(IFileGenerator):

    _extension = 'html'

    def __init__(self, folder_path: str | Path, template_name: str) -> None:
        env = Environment(loader=FileSystemLoader(folder_path, encoding='utf-8'), enable_async=True)
        self._template = env.get_template(template_name)

    @property
    def template(self) -> Template:
        return self._template

    async def generate_file(self, questions: dict, replies: dict) -> bytes:
        replies_keys = sorted(replies.keys(), key=lambda x: datetime.strptime(x, '%d.%m'))
        replies_list = [questions] + [replies[key] for key in replies_keys]
        start_date = replies_keys[0]
        end_date = replies_keys[-1]

        str_file = await self.template.render_async(
            start_date=start_date,
            end_date=end_date,
            replies_list=replies_list,
            question_list=list(questions.keys())
        )
        return str_file.encode(encoding='utf-8')
