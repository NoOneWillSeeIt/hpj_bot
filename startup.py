import logging

from typer import Typer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


typer = Typer()


@typer.command()
def tgbot(host: str, port: int = 443, remote_url: str = "", test_config: bool = False):
    from telegram.constants import SUPPORTED_WEBHOOK_PORTS

    from tg_bot.bot import start_bot

    if port not in SUPPORTED_WEBHOOK_PORTS:
        logging.error(
            f"Port must be one of the supported by telegram: {SUPPORTED_WEBHOOK_PORTS}"
        )
        return

    start_bot(host, port, remote_url, test_config)


@typer.command()
def webapp(host: str = "localhost", port: int = 8000, test_config: bool = False):
    import uvicorn

    from webapp.core.settings import DB_FOLDER, init_test_settings
    from webapp.fastapi_app import app

    if not DB_FOLDER.exists():
        DB_FOLDER.mkdir()

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
