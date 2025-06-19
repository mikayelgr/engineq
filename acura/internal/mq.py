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

import json
import logging
import asyncio

import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractIncomingMessage

from internal.chain import curate
from internal.models.dao import SubscribersDAO

__logger = logging.getLogger(__name__)


async def start_consuming(mq: AbstractRobustConnection) -> None:
    """
    Establish a channel to the RabbitMQ queue and consume messages indefinitely,
    creating async tasks for each message to be processed.
    """

    __logger.info("Starting message consumption from RabbitMQ...")
    channel = await mq.channel()
    queue = await channel.declare_queue("acura", durable=True, auto_delete=False)
    sem = asyncio.Semaphore(5)  # Limit concurrent processing to 5 tasks
    tasks: set[asyncio.Task] = set()

    async def process_with_semaphore(message: AbstractIncomingMessage):
        async with sem:
            await __process_message(message)

    async with queue.iterator() as iterator:
        try:
            async for message in iterator:
                task = asyncio.create_task(process_with_semaphore(message))
                tasks.add(task)
                task.add_done_callback(lambda t: tasks.discard(t))
        except asyncio.CancelledError:
            __logger.info("Shutdown triggered, canceling tasks...")
        finally:
            __logger.info("Waiting for all tasks to complete...")
            for task in tasks:
                task.cancel()


async def __process_message(msg: AbstractIncomingMessage) -> None:
    try:
        async with msg.process(ignore_processed=True):
            license_key = __extract_license_key(msg)
            if not license_key:
                raise ValueError("License key not provided in the message.")

            subscriber = await SubscribersDAO.get_subscriber_by_license(license_key)
            if not subscriber:
                raise ValueError(
                    "No subscriber found with the provided license key.")

            try:
                n_added_items = await curate(subscriber.id)
            except Exception as e:
                raise RuntimeError(f"Error during curation: {e}")

            if n_added_items > 0:
                await msg.ack()
            else:
                # If no items were added, we can choose to reject the message and
                # requeue it for later processing.
                await msg.reject()

    except Exception as e:
        __logger.error("Error processing message: %s", e)
        try:
            # Reject the message to prevent re-queuing
            await msg.reject(requeue=False)
        except aio_pika.exceptions.MessageProcessError as e:
            __logger.error("Message already processed: %s", e)


def __extract_license_key(msg: AbstractIncomingMessage) -> str | None:
    """
    Extract the license key from the message body.
    """

    try:
        return json.loads(msg.body)["license"]
    except json.JSONDecodeError:
        __logger.error("Failed to decode message body as JSON.")
        return None
