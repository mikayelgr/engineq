# AVOID MOVING THESE LINES TO OTHER PLACES AS THE PARSING OF THE
# .ENV FILE FAILS IN MOST CASES DUE TO SOME REASONS.
from dotenv import load_dotenv, find_dotenv  # nopep8
load_dotenv(find_dotenv())  # nopep8

import conf
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import amqp
from mq import consume_message


def main():
    # Connecting to the database
    engine = create_engine(conf.Config().POSTGRES_URL, echo=False, isolation_level="AUTOCOMMIT")
    with Session(engine) as pg:
        with amqp.Connection() as mq:
            c = mq.channel()

            def consume(m: amqp.Message):
                try:
                    # Message handling is done separately
                    consume_message(m, pg)
                    # Acknowledging the request after processing, so that we don't
                    # redeliver it the next time and waste resources on processing.
                    c.basic_ack(m.delivery_tag)
                except Exception as e:
                    print(e)
                    c.basic_reject(m.delivery_tag, requeue=False)

            c.basic_consume(queue="acura", callback=consume)
            while True:
                mq.drain_events()

    engine.dispose()  # Closing SQL connection


if __name__ == "__main__":
    main()
