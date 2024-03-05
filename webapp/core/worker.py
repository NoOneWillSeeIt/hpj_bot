import json
import logging
from collections import namedtuple

import requests
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from survey.hpj_questions import Questions
from webapp.core.db_helper import DatabaseHelper
from webapp.core.models import JournalEntry
from webapp.journal_view.html_generator import HTMLGenerator

from .settings import DbSettings, JinjaSettings, RedisSettings

TaskInfo = namedtuple("TaskInfo", ["user_id", "channel", "channel_id", "start", "end"])


def read_entries_from_db(session: Session, info: TaskInfo) -> list[JournalEntry]:
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.user_id == info.user_id)
        .where(info.start <= JournalEntry.date <= info.end)
    )
    return session.scalars(stmt).all()


def parse_task_info(task_info: str) -> TaskInfo:
    try:
        splitted = task_info.split(";")
        return TaskInfo(*splitted)
    except Exception:
        logging.error(f'Can\'t parse task info: "{task_info}"')

    return TaskInfo(*[None] * 5)


def worker(
    redis_settings: RedisSettings,
    db_settings: DbSettings,
    jinja_settings: JinjaSettings,
):
    redis = Redis(host=redis_settings.url, port=redis_settings.port)
    db_helper = DatabaseHelper(db_settings.url, db_settings.echo)
    html_gen = HTMLGenerator(
        folder_path=jinja_settings.templates_dir,
        template_name=jinja_settings.journal_tmpl,
        questions=Questions.to_dict(),
    )

    while True:
        task_info_key = redis.blpop(["gen_report_queue"])
        info = parse_task_info(task_info_key)

        entry_rows = []
        with db_helper.session_context() as session:
            entry_rows = read_entries_from_db(session, info)

        if not entry_rows:
            continue

        out_file = html_gen.generate(
            replies={row.date: json.loads(row.entry) for row in entry_rows},
        )
        filename = html_gen.gen_filename(f"{info.start}-{info.end}")

        channel_url = redis.get(f"{info.channel}_url")
        requests.post(
            url=f"{channel_url}/{info.channel_id}",
            files={"upload_file": (filename, out_file, "multipart/form-data")},
        )
