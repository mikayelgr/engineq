import json
import sqlalchemy as db
from models import Subscribers
import chain
from sqlalchemy.ext.asyncio import AsyncConnection
import aio_pika


async def consume(msg: aio_pika.abc.AbstractIncomingMessage, pg: AsyncConnection):
    try:
        b = json.loads(msg.body)
    except:
        raise Exception("Invalid JSON body provided in AMQP message")

    if ("license" not in b) or (b["license"] == "") or (b["license"] is None):
        raise Exception("License key was not provided")

    r = await pg.execute(db.select(Subscribers).where(Subscribers.license == b["license"]))
    s = r.one()
    if s is None:
        raise Exception("No subscriber found with the given license")

    if await chain.compose(s.id, b["prompt"], chain.WrappedSQLASession(session=pg)) is None:
        raise Exception("Something wrong happened during generation...")
