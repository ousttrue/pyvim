import logging
import traceback
import asyncio
from typing import NamedTuple
from .editor_layout.editor_window.editor_buffer import EditorBuffer
from pyvim.editor import get_editor
from .commands.handler import handle_command

logger = logging.getLogger(__name__)
QUEUE = asyncio.Queue()


class Command(NamedTuple):
    input: str


class Message(NamedTuple):
    message: str


class NewBuffer(NamedTuple):
    editor_buffer: EditorBuffer

    def __str__(self) -> str:
        return f'NewBuffer({self.editor_buffer.location})'


def enqueue(value):
    QUEUE.put_nowait(value)


def enqueue_command(input: str):
    enqueue(Command(input))


def enqueue_new_buffer(eb: EditorBuffer):
    enqueue(NewBuffer(eb))


async def worker():
    logger.info('start worker')
    while True:
        value = await QUEUE.get()
        logger.debug(value)
        try:
            match value:
                case Command(input):
                    handle_command(input)

                case Message(msg):
                    get_editor().show_message(msg)

                case NewBuffer(eb):
                    # launch LSP
                    get_editor().launch(eb)

                case None:
                    logger.info('exit worker')
                    break

                case _:
                    raise RuntimeError('unknown')
        except Exception as e:
            logger.exception(e)
            raise

