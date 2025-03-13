# AVOID MOVING THESE LINES TO OTHER PLACES AS THE PARSING OF THE
# .ENV FILE FAILS IN MOST CASES DUE TO SOME REASONS.
from dotenv import load_dotenv, find_dotenv  # nopep8
load_dotenv(find_dotenv())  # nopep8

from sqlalchemy.ext.asyncio import create_async_engine
from internal.mq import consume
import aio_pika
import asyncio


async def main():
    try:
        # Connecting to the database
        sql_conn = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5431/engineq",
                                       echo=False, isolation_level="AUTOCOMMIT")
        async with sql_conn.begin() as pg:
            async with await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/") as mq:
                chan = await mq.channel()
                queue = await chan.declare_queue("acura", durable=True, auto_delete=False)
                async with queue.iterator() as iterator:
                    async for msg in iterator:
                        async with msg.process(ignore_processed=True):
                            try:
                                await consume(msg, pg)
                                await msg.ack()
                            except Exception as e:
                                print("AMQP Error During Processing:", e)
                                await msg.reject(requeue=False)
    except:
        pass
    finally:
        await mq.close()
        await pg.close()
        await sql_conn.dispose()  # Closing SQL connection gracefully


if __name__ == "__main__":
    asyncio.run(main())
