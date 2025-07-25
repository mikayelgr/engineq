"""
EngineQ: An AI-enabled music management system.
Copyright (C) 2025  Mikayel Grigoryan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

For inquiries, contact: michael.grigoryan25@gmail.com
"""

import logging
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncConnection
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, ClassVar
from internal.conf import Config
from dataclasses import dataclass


@dataclass
class SQLDatabase:
    """
    Class that manages global PostgreSQL connections using classmethods.
    No instance needed - all methods are called on the class directly.
    """

    __logger = logging.getLogger(__name__)
    # Class variables for the connection state
    __engine: ClassVar[Optional[AsyncEngine]] = None
    _connection: ClassVar[Optional[AsyncConnection]] = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize the database engine if not already done."""
        if cls.__engine is None:
            config = Config()
            cls.__engine = create_async_engine(
                config.POSTGRES_URL,
                echo=config.DEBUG,
                isolation_level="AUTOCOMMIT"
            )
            cls.__logger.info("Database engine initialized")

    @classmethod
    async def get_connection(cls) -> AsyncConnection:
        """
        Get the global connection or create a new one.
        """
        if cls.__engine is None:
            cls.initialize()

        if cls._connection is None or cls._connection.closed:
            cls._connection = await cls.__engine.connect().start()  # type: ignore
            cls.__logger.info("New database connection established")
        return cls._connection

    @classmethod
    @asynccontextmanager
    async def connection(cls) -> AsyncGenerator[AsyncConnection, None]:
        """
        Context manager for database connections.
        """
        conn = await cls.get_connection()
        try:
            yield conn
        except Exception as e:
            cls.__logger.exception(f"Error during database operation: {e}")
            raise

    @classmethod
    async def close(cls) -> None:
        """
        Close the database connection and dispose of the engine.
        """
        if cls._connection is not None and not cls._connection.closed:
            await cls._connection.close()
            cls._connection = None
            cls.__logger.info("Database connection closed")

        if cls.__engine is not None:
            await cls.__engine.dispose()
            cls.__engine = None
            cls.__logger.info("Database engine disposed")
