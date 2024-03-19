import logging

from typer import Typer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


typer = Typer()


@typer.command(name="tgbot")
def tgbot(host: str, port: int, remote_url: str = '', test_config: bool = False):
    from tg_bot.bot import start_bot
    start_bot(host, port, remote_url, test_config)


@typer.command()
def webapp(host: str = "localhost", port: int = 8000, test_config: bool = False):
    import os

    import uvicorn

    from webapp.core.settings import DB_FOLDER, init_test_settings
    from webapp.fastapi_app import app

    dirs = os.listdir()
    if DB_FOLDER not in dirs:
        os.mkdir(DB_FOLDER)

    if test_config:
        init_test_settings()

    uvicorn.run(app, host=host, port=port)


@typer.command()
def workers(count: int = 4, test_config: bool = False):
    from webapp.workers.reports.worker import worker

    worker(count, test_config)


@typer.command()
def scheduler(test_config: bool = False):
    from webapp.workers.scheduler.worker import worker

    worker(test_config)


if __name__ == "__main__":
    typer()
