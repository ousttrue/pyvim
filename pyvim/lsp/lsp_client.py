import pathlib
import asyncio.subprocess
import asyncio.events
import logging
import json
from . import protocol
logger = logging.getLogger(__name__)

PYTHON = pathlib.Path('C:/Python310/Scripts/pyls.exe')


class LSPClient:
    def __init__(self, loop: asyncio.events.AbstractEventLoop, root: pathlib.Path) -> None:
        self.loop = loop
        self.proc = None
        self.root = root
        self.request_id = 1

    def launch(self, path: pathlib.Path, *args):
        self.loop.create_task(self._launch_async(path, *args))

    async def _launch_async(self, path, *args):
        self.proc = await asyncio.subprocess.create_subprocess_exec(path, *args,
                                                                    stdin=asyncio.subprocess.PIPE,
                                                                    stdout=asyncio.subprocess.PIPE,
                                                                    stderr=asyncio.subprocess.PIPE,
                                                                    )
        logger.info(f'launch: {path} {args}')
        self.loop.create_task(self._out_async())
        self.loop.create_task(self._err_async())

        # initialize
        value = protocol.InitializeParams(
            rootUri=str(self.root),
            capabilities={}
        )
        request = self._make_request("initialize", value)
        await self._request_async(json.dumps(request).encode('utf-8'))

    def _make_request(self, method: str, params) -> protocol.Request:
        request_id = self.request_id
        self.request_id += 1
        return protocol.Request(
            jsonrpc="2.0",
            id=request_id,
            method=method,
            params=params
        )

    async def _request_async(self, body: bytes):
        assert(self.proc)
        assert(self.proc.stdin)
        header = f'Content-Length: {len(body)}\r\n'
        self.proc.stdin.write(header.encode('ascii'))
        self.proc.stdin.write(b'\r\n')
        self.proc.stdin.write(body)

    async def _out_async(self):
        if not self.proc:
            return
        if not self.proc.stdout:
            return
        logger.debug('read stdout')
        while True:
            if self.proc.stdout.at_eof():
                logger.error('end stdout')
                break
            l = await self.proc.stdout.readline()
            logger.info(l)

    async def _err_async(self):
        if not self.proc:
            return
        if not self.proc.stderr:
            return
        logger.debug('read stderr')
        while True:
            if self.proc.stderr.at_eof():
                logger.error('end stderr')
                break
            l = await self.proc.stderr.readline()
            logger.error(l)
