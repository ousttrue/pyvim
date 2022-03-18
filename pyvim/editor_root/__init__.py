from typing import Tuple
import pathlib
import prompt_toolkit.layout
import prompt_toolkit.filters
import prompt_toolkit.widgets
import prompt_toolkit.layout.processors
from .tabs_control import TabsToolbar


class EditorRoot:
    def __init__(self, config_directory: pathlib.Path) -> None:
        from .window_arrangement import WindowArrangement
        self.window_arrangement = WindowArrangement(config_directory)

        from .welcome_message import WelcomeMessageWindow, WELCOME_MESSAGE_HEIGHT, WELCOME_MESSAGE_WIDTH
        from .buffer_list import BufferListOverlay, _bufferlist_overlay_visible
        from .message_toolbar import MessageToolbarBar
        from pyvim.editor import get_editor
        editor = get_editor()

        from ..commands.commandline import CommandLine
        self.commandline = CommandLine(config_directory)

        self.container = prompt_toolkit.layout.FloatContainer(
            content=self.window_arrangement,
            floats=[
                prompt_toolkit.layout.Float(xcursor=True, ycursor=True,
                                            content=prompt_toolkit.layout.menus.CompletionsMenu(max_height=12,
                                                                                                scroll_offset=2,
                                                                                                extra_filter=~self.commandline.has_focus)),
                prompt_toolkit.layout.Float(
                    content=BufferListOverlay(), bottom=1, left=0),
                prompt_toolkit.layout.Float(bottom=1, left=0, right=0, height=1,
                                            content=prompt_toolkit.layout.ConditionalContainer(
                                                prompt_toolkit.widgets.CompletionsToolbar(),
                                                filter=self.commandline.has_focus &
                                                ~_bufferlist_overlay_visible() &
                                                prompt_toolkit.filters.Condition(lambda: editor.show_wildmenu))),
                prompt_toolkit.layout.Float(bottom=1, left=0, right=0, height=1,
                                            content=prompt_toolkit.widgets.ValidationToolbar()),
                prompt_toolkit.layout.Float(bottom=1, left=0, right=0, height=1,
                                            content=MessageToolbarBar(editor)),
                prompt_toolkit.layout.Float(content=WelcomeMessageWindow(self.window_arrangement),
                                            height=WELCOME_MESSAGE_HEIGHT,
                                            width=WELCOME_MESSAGE_WIDTH),
            ]
        )

        self.tabbar = TabsToolbar(self.window_arrangement)

    def __pt_container__(self):
        return self.container
