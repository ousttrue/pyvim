from typing import Dict, Optional
import logging
from prompt_toolkit.application.current import get_app
import prompt_toolkit.layout
from ..window_arrangement.editor_buffer import EditorBuffer
from ..lsp import lsp_client
logger = logging.getLogger(__name__)
STYLE = 'bg:#DDDDDD #000000'


class LspStatus:
    def __init__(self) -> None:
        self.controller = prompt_toolkit.layout.controls.FormattedTextControl(
            self.get_text)
        self.container = prompt_toolkit.layout.Window(
            self.controller, height=4, style=STYLE)

        self._lsp: Dict[str, lsp_client.LSPClient] = {}
        self._current: Optional[lsp_client.LSPClient] = None

        from ..event_dispatcher import DISPATCHER, EventType
        DISPATCHER.register(EventType.NewEditorBuffer, self.launch)

        self.loop = None

    def __pt_container__(self) -> prompt_toolkit.layout.Container:
        return self.container

    def get_text(self):
        if not self._current:
            return ''
        return [('', 'lsp ')] + self._current.get_text()

    def launch(self, eb: EditorBuffer):
        ft = eb.filetype
        logger.info(f'launch {ft}')
        assert(eb.location)

        lsp = self._lsp.get(ft)
        if lsp:
            return

        lsp = lsp_client.launch(ft, eb.location.parent)
        if lsp:
            self._lsp[ft] = lsp
            self._current = lsp
