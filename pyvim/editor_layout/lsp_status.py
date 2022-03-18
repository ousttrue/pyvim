from typing import Dict
import logging
from prompt_toolkit.application.current import get_app
import prompt_toolkit.layout
from ..window_arrangement.editor_buffer import EditorBuffer
from ..lsp import lsp_client
logger = logging.getLogger(__name__)
STYLE = 'bg:#DDDDDD #000000'


class LspStatus:
    def __init__(self) -> None:
        self.text = [('', 'lsp')]
        self.controller = prompt_toolkit.layout.controls.FormattedTextControl(
            lambda: self.text)
        self.container = prompt_toolkit.layout.Window(
            self.controller, height=4, style=STYLE)

        self.lsp: Dict[str, lsp_client.LSPClient] = {}

        from ..event_dispatcher import DISPATCHER, EventType
        DISPATCHER.register(EventType.NewEditorBuffer, self.launch)

        self.loop = None

    def __pt_container__(self) -> prompt_toolkit.layout.Container:
        return self.container

    def launch(self, eb: EditorBuffer):
        ft = eb.filetype
        if ft == '.py':
            if ft not in self.lsp:
                logger.info('launch lsp for python')
                loop = get_app().loop
                assert(loop)
                assert(eb.location)
                lsp = lsp_client.LSPClient(loop, eb.location.parent)
                lsp.launch(lsp_client.PYTHON)
                self.lsp[ft] = lsp
        else:
            logger.warning(f'unknown file type: {ft}')
