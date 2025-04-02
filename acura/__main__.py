# AVOID MOVING THESE LINES TO OTHER PLACES AS THE PARSING OF THE
# .ENV FILE FAILS IN MOST CASES DUE TO SOME REASONS.
from dotenv import load_dotenv, find_dotenv  # nopep8
load_dotenv(find_dotenv())  # nopep8

import logging
from sqlalchemy.ext.asyncio import create_async_engine
from internal.mq import consume
import aio_pika
import asyncio
from pydantic_ai import Agent
import logfire
from internal.conf import Config
import os
import sqlalchemy.exc


async def process_message(msg, pg, conf, logger):
    """
    Process a single RabbitMQ message.
    """
    try:
        async with msg.process(ignore_processed=True):
            await consume(msg, pg, conf)
            await msg.ack()
    except Exception as e:
        logger.error("AMQP Error During Processing: %s", e)
        try:
            await msg.reject(requeue=False)
        except aio_pika.exceptions.MessageProcessError as mpe:
            logger.error("Message already processed: %s", mpe)


async def main():
    conf = Config()
    logging.basicConfig(
        level=logging.ERROR if conf.DEBUG else logging.INFO | logging.ERROR | logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    logfire.configure(token=conf.LOGFIRE_TOKEN)
    Agent.instrument_all()  # used for pydanticai logging

    logger = logging.getLogger(__name__)
    # Limit concurrency to 10 tasks
    semaphore = asyncio.Semaphore(os.cpu_count())

    async def limited_process_message(msg, pg, conf, logger):
        async with semaphore:
            await process_message(msg, pg, conf, logger)

    # Connecting to PostgreSQL
    postgres_engine = create_async_engine(
        conf.POSTGRES_URL, echo=conf.DEBUG, isolation_level="AUTOCOMMIT")

    try:
        pg = await postgres_engine.connect().start()
        mq = await aio_pika.connect_robust(conf.AMQP_URL)

        chan = await mq.channel()
        queue = await chan.declare_queue("acura", durable=True, auto_delete=False)

        async with queue.iterator() as iterator:
            tasks = set()
            async for msg in iterator:
                # Create a task for each message
                task = asyncio.create_task(
                    limited_process_message(msg, pg, conf, logger))
                tasks.add(task)

                # Remove completed tasks from the set
                task.add_done_callback(tasks.discard)

    except aio_pika.exceptions.AMQPConnectionError as e:
        logger.error("AMQP Connection Error: %s", e)
    except sqlalchemy.exc.SQLAlchemyError as e:
        logger.error("PSQL Runtime Error: %s", e)
    except (KeyboardInterrupt, asyncio.CancelledError, SystemExit):
        print("Shutting down acura...")
        await iterator.close()  # Stopping the consumption of the iterator
    finally:
        await pg.close()
        await postgres_engine.dispose()
        await mq.close()


if __name__ == "__main__":
    asyncio.run(main())
