from internal.models.sql import SQLDatabase
from pythonjsonlogger.json import JsonFormatter
import internal.mq
from internal.conf import Config
import logfire
from pydantic_ai import Agent
import signal
import asyncio
import aio_pika
import logging


async def main() -> int:
    conf = Config()
    logging.basicConfig(level=logging.ERROR if conf.DEBUG else logging.INFO)

    formatter = JsonFormatter(
        "{levelname}{name}{filename}:{lineno}{asctime}{message}", style="{")
    logging.getLogger().handlers[0].setFormatter(formatter)

    stop_event = asyncio.Event()

    def handle_shutdown_signal():
        logging.getLogger(__name__).info("Shutdown signal received...")
        stop_event.set()

    # Register signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown_signal)

    try:
        # Connecting to PostgreSQL
        await SQLDatabase.get_connection()
        logging.getLogger(__name__).info("Connected to PostgreSQL...")
    except Exception as e:
        logging.getLogger(__name__).error("PostgreSQL Connection Error: %s", e)
        return -1

    try:
        mq = await aio_pika.connect_robust(conf.AMQP_URL)
        logging.getLogger(__name__).info("Connected to RabbitMQ...")
    except Exception as e:
        logging.getLogger(__name__).error("AMQP Connection Error: %s", e)
        await SQLDatabase.close()
        return -1

    exit_code = 0
    try:
        logging.info("Acura is starting...")
        logging.info("Logfire is initializing...")
        logfire.configure(token=conf.LOGFIRE_TOKEN, service_name="acura")
        Agent.instrument_all()  # used for pydanticai logging

        # Start consuming messages and wait for the stop event
        consume_tasks = asyncio.create_task(
            internal.mq.start_consuming(mq))
        await stop_event.wait()
        consume_tasks.cancel()
        try:
            await consume_tasks
        except asyncio.CancelledError:
            logging.getLogger(__name__).info("Stopping message consumption...")
    except Exception as e:
        logging.getLogger(__name__).error("Unhandled error: %s", e)
        exit_code = -1
    finally:
        logging.getLogger(__name__).info("Acura is shutting down...")
        # Gracefully close the PostgreSQL connection
        await mq.close()
        await SQLDatabase.close()

    return exit_code


if __name__ == "__main__":
    code = asyncio.run(main())
    exit(code)
