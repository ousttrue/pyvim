"""
The actual layout for the renderer.
"""
import pathlib
import prompt_toolkit.filters
import prompt_toolkit.layout
import prompt_toolkit.widgets
import prompt_toolkit.layout.menus
import prompt_toolkit.layout.processors


__all__ = (
    'EditorLayout',
)


class EditorLayout(object):
    """
    The main layout class.
    """

    def __init__(self, config_directory: pathlib.Path):
        from ..editor_root import EditorRoot
        from .report_message_toolbar import ReportMessageToolbar
        from .simple_arg_toolbar import SimpleArgToolbar
        from .logger import LoggerWindow

        self.editor_root = EditorRoot(config_directory)
        editor_layout = prompt_toolkit.layout.FloatContainer(
            content=prompt_toolkit.layout.HSplit([
                self.editor_root.tabbar,
                self.editor_root,
                self.editor_root.commandline,
                ReportMessageToolbar(self.editor_root.commandline.has_focus),
                prompt_toolkit.widgets.SystemToolbar(),
                self.editor_root.window_arrangement.searchline,
            ]),
            floats=[
                prompt_toolkit.layout.Float(right=0, height=1, bottom=0, width=5,
                                            content=SimpleArgToolbar()),
            ]
        )

        logger_window = LoggerWindow()
        editor_logger = prompt_toolkit.layout.HSplit([
            editor_layout,
            logger_window,
        ])

        # background color
        self.container = prompt_toolkit.layout.FloatContainer(
            content=prompt_toolkit.layout.Window(
                char=' ',
                ignore_content_width=True,
                ignore_content_height=True,
            ),
            floats=[
                prompt_toolkit.layout.Float(
                    editor_logger,
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
