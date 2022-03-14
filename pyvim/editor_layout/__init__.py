"""
The actual layout for the renderer.
"""
import prompt_toolkit.filters
import prompt_toolkit.layout
import prompt_toolkit.widgets
import prompt_toolkit.layout.menus
import prompt_toolkit.layout.processors
import pyvim.window_arrangement as window_arrangement


__all__ = (
    'EditorLayout',
)


class EditorLayout(object):
    """
    The main layout class.
    """

    def __init__(self):
        from ..window_arrangement import WindowArrangement
        self.window_arrangement = WindowArrangement()

        from .editor_root import EditorRoot
        self.editor_root = EditorRoot(self.window_arrangement)

        from .tabs_control import TabsToolbar
        from .command_line import CommandLine
        from .report_message_toolbar import ReportMessageToolbar
        from .simple_arg_toolbar import SimpleArgToolbar

        root = prompt_toolkit.layout.FloatContainer(
            content=prompt_toolkit.layout.HSplit([
                TabsToolbar(self.window_arrangement),
                self.editor_root,
                CommandLine(),
                ReportMessageToolbar(),
                prompt_toolkit.widgets.SystemToolbar(),
                self.editor_root.search_toolbar,
            ]),
            floats=[
                prompt_toolkit.layout.Float(right=0, height=1, bottom=0, width=5,
                                            content=SimpleArgToolbar()),
            ]
        )

        # background color
        self.container = prompt_toolkit.layout.FloatContainer(
            content=prompt_toolkit.layout.Window(
                char=' ',
                ignore_content_width=True,
                ignore_content_height=True,
            ),
            floats=[
                prompt_toolkit.layout.Float(
                    root,
                    transparent=True,
                    left=0,
                    right=0,
                    top=0,
                    bottom=0
                ),
            ],
        )

    def __pt_container__(self):
        return self.container
