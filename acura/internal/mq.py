import json
import sqlalchemy as db
from internal.models import Subscribers
import internal.chain as chain
from sqlalchemy.ext.asyncio import AsyncConnection
import aio_pika


async def consume(msg: aio_pika.abc.AbstractIncomingMessage, pg: AsyncConnection):
    try:
        parsed_message = json.loads(msg.body)
    except:
        raise Exception("Invalid JSON body provided in AMQP message")

    if ("license" not in parsed_message) or (parsed_message["license"] == "") or (parsed_message["license"] is None):
        raise Exception("License key was not provided")

    r = await pg.execute(db.select(Subscribers).where(Subscribers.license == parsed_message["license"]))
    s = r.one()
    if s is None:
        raise Exception("No subscriber found with the given license")

    try:
        await chain.compose(s.id, chain.WrappedSQLAClient(conn=pg))
    except Exception as e:
        raise Exception(f"Something wrong happened during generation: {e}")
