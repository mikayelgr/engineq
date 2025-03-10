import models
import conf
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


async def main():
    print(conf.Config().__dict__)
    # Connecting to the database
    engine = create_async_engine(
        "postgresql+asyncpg://"+conf.Config().POSTGRES_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    await engine.dispose()


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.stop()
