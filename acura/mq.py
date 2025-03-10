import json
import sqlalchemy as db
from models import Subscribers
import chain
import amqp
from sqlalchemy.orm import Session


def consume_message(m: amqp.Message, pg: Session):
    b = json.loads(m.body)
    if "license" not in b:
        raise Exception("License key was not provided")

    q = db.select(Subscribers).where(Subscribers.license == b["license"])
    s = pg.execute(q).scalars().first()
    if s is None:
        raise Exception("No subscriber found with the given license")

    if not chain.compose(s.id, b["prompt"], chain.WrappedSQLASession(session=pg)):
        raise Exception("Something wrong happened during generation...")
