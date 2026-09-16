import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from aiogram import Bot
from fastapi import FastAPI

from app.bot import build_dispatcher
from app.config import get_settings
from app.storage import Storage
from app.notifications import run_notification_worker
from app.web import register_routes


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "bot.log", encoding="utf-8"),
    ],
)

settings = get_settings()

storage = Storage(
    settings.database_file,
    settings.oauth_state_secret,
)

migrated = storage.migrate_legacy_json(
    settings.google_credentials_file
)

if migrated:
    logging.info(
        "Migrated %s Google credential record(s) "
        "from v4 JSON to SQLite",
        migrated,
    )

bot = Bot(token=settings.bot_token)
dp = build_dispatcher(settings, storage)

polling_task: asyncio.Task | None = None
notification_task: asyncio.Task | None = None


def polling_finished(task: asyncio.Task) -> None:
    """
    Обязательно забираем результат фоновой задачи,
    чтобы исключение polling не потерялось.
    """
    if task.cancelled():
        logging.warning("Telegram polling task cancelled")
        return

    try:
        task.result()
    except Exception:
        logging.exception("TELEGRAM POLLING CRASHED")
    else:
        logging.warning(
            "Telegram polling finished unexpectedly "
            "without an exception"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task, notification_task

    logging.info("Starting Telegram polling...")

    polling_task = asyncio.create_task(
        dp.start_polling(
            bot,
            handle_signals=False,
        ),
        name="telegram-polling",
    )

    polling_task.add_done_callback(
        polling_finished
    )

    notification_task = asyncio.create_task(
        run_notification_worker(bot, storage),
        name="telegram-notification-worker",
    )

    try:
        yield

    finally:
        logging.info("Stopping Telegram polling...")

        if notification_task and not notification_task.done():
            notification_task.cancel()
            try:
                await notification_task
            except asyncio.CancelledError:
                pass
            except Exception:
                logging.exception("Notification worker error during shutdown")

        if polling_task and not polling_task.done():
            await dp.stop_polling()

            try:
                await polling_task
            except Exception:
                logging.exception(
                    "Polling error during shutdown"
                )

        await bot.session.close()


app = FastAPI(
    title="Telegram Calendar Bot",
    lifespan=lifespan,
)

register_routes(
    app,
    settings,
    bot,
    storage,
)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
    )