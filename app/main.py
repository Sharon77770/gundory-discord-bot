import asyncio
import logging
import signal

from app.bot.bot import BriarBot
from app.config import Settings
from app.database.database import configure_database, dispose_database
from app.logging_config import configure_logging


async def run() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    logger = logging.getLogger("briar.main")
    settings.ensure_data_directory()
    configure_database(settings.database_url)
    bot = BriarBot(settings)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, RuntimeError):
            # Windows does not expose asyncio signal handlers for every signal.
            pass
    bot_task = asyncio.create_task(bot.start(settings.discord_token))

    def wake_on_bot_exit(task: asyncio.Task) -> None:
        if not task.cancelled() and task.exception() is not None:
            error = task.exception()
            logger.error("Discord connection stopped: %s", error,
                         exc_info=(type(error), error, error.__traceback__))
        stop_event.set()

    bot_task.add_done_callback(wake_on_bot_exit)
    try:
        await stop_event.wait()
    finally:
        await bot.close()
        bot.briar_scheduler.stop()
        dispose_database()
        if not bot_task.done():
            bot_task.cancel()
        await asyncio.gather(bot_task, return_exceptions=True)
        logger.info("Briar Bot stopped")


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
