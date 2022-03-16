import logging
import asyncio
from typing import NamedTuple
logger = logging.getLogger(__name__)
QUEUE = asyncio.Queue()


class Command(NamedTuple):
    input: str


def enqueue_command(input: str):
    QUEUE.put_nowait(Command(input))


async def worker():
    logger.info('start worker')
    while True:
        value = await QUEUE.get()
        logger.debug(value)
        match value:
            case Command(input):
                from .commands.handler import handle_command
                handle_command(input)

            case None:
                logger.info('exit worker')
                break

            case _:
                raise RuntimeError('unknown')
