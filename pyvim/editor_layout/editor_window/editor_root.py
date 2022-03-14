import pathlib
import sys
from functools import partial
from prompt_toolkit.application.current import get_app
import prompt_toolkit.layout
import prompt_toolkit.filters
import prompt_toolkit.widgets
import prompt_toolkit.layout.processors


def _try_char(character, backup, encoding=sys.stdout.encoding):
    """
    Return `character` if it can be encoded using sys.stdout, else return the
    backup character.
    """
    if character.encode(encoding, 'replace') == b'?':
        return backup
    else:
        return character


TABSTOP_DOT = _try_char('\u2508', '.')


class EditorRoot:
    def __init__(self, config_directory: pathlib.Path) -> None:
        # Mapping from (`window_arrangement.Window`, `EditorBuffer`) to a frame
        # (Layout instance).
        # We keep this as a cache in order to easily reuse the same frames when
        # the layout is updated. (We don't want to create new frames on every
        # update call, because that way, we would loose some state, like the
        # vertical scroll offset.)
        self._frames = {}

        from .window_arrangement import WindowArrangement
        self.window_arrangement = WindowArrangement()

        from ..welcome_message import WelcomeMessageWindow, WELCOME_MESSAGE_HEIGHT, WELCOME_MESSAGE_WIDTH
        from ..buffer_list import BufferListOverlay, _bufferlist_overlay_visible
        from ..message_toolbar import MessageToolbarBar
        from pyvim.editor import get_editor
        editor = get_editor()

        from ...commands.command_line import CommandLine
        self.commandline = CommandLine(config_directory)

        self.container = prompt_toolkit.layout.FloatContainer(
            content=prompt_toolkit.layout.VSplit([
                prompt_toolkit.layout.Window(
                    prompt_toolkit.layout.BufferControl())  # Dummy window
            ]),
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

        self.search_toolbar = prompt_toolkit.widgets.SearchToolbar(
            vi_mode=True, search_buffer=editor.search_buffer)
        self.search_control = self.search_toolbar.control

    def __pt_container__(self):
        return self.container

    def update(self):
        """
        Update layout to match the layout as described in the
        WindowArrangement.
        """
        # Start with an empty frames list everytime, to avoid memory leaks.
        existing_frames = self._frames
        self._frames = {}

        from . import window_arrangement

        def create_layout_from_node(node):
            if isinstance(node, window_arrangement.Window):
                # Create frame for Window, or reuse it, if we had one already.
                key = (node, node.editor_buffer)
                frame = existing_frames.get(key)
                if frame is None:
                    frame, pt_window = self._create_window_frame(
                        node.editor_buffer)

                    # Link layout Window to arrangement.
                    node.pt_window = pt_window

                self._frames[key] = frame
                return frame

            elif isinstance(node, window_arrangement.VSplit):
                return prompt_toolkit.layout.VSplit(
                    [create_layout_from_node(n) for n in node],
                    padding=1,
                    padding_char=self._get_vertical_border_char(),
                    padding_style='class:frameborder')

            if isinstance(node, window_arrangement.HSplit):
                return prompt_toolkit.layout.HSplit([create_layout_from_node(n) for n in node])

        layout = create_layout_from_node(
            self.window_arrangement.active_tab.root)
        self.container.content = layout

    def _create_window_frame(self, editor_buffer):
        """
        Create a Window for the buffer, with underneat a status bar.
        """
        @prompt_toolkit.filters.Condition
        def wrap_lines():
            from ...editor import get_editor
            editor = get_editor()
            return editor.wrap_lines

        from ...editor import get_editor
        editor = get_editor()
        window = prompt_toolkit.layout.Window(
            self._create_buffer_control(editor_buffer),
            allow_scroll_beyond_bottom=True,
            scroll_offsets=prompt_toolkit.layout.ScrollOffsets(
                left=0, right=0,
                top=(lambda: editor.scroll_offset),
                bottom=(lambda: editor.scroll_offset)),
            wrap_lines=wrap_lines,
            left_margins=[prompt_toolkit.layout.ConditionalMargin(
                margin=prompt_toolkit.layout.NumberedMargin(
                    display_tildes=True,
                    relative=prompt_toolkit.filters.Condition(lambda: editor.relative_number)),
                filter=prompt_toolkit.filters.Condition(lambda: editor.show_line_numbers))],
            cursorline=prompt_toolkit.filters.Condition(
                lambda: editor.cursorline),
            cursorcolumn=prompt_toolkit.filters.Condition(
                lambda: editor.cursorcolumn),
            colorcolumns=(
                lambda: [prompt_toolkit.layout.ColorColumn(pos) for pos in editor.colorcolumn]),
            ignore_content_width=True,
            ignore_content_height=True,
            get_line_prefix=partial(self._get_line_prefix, editor_buffer.buffer))

        from ..window_statusbar import WindowStatusBar
        from ..window_statusbar_ruler import WindowStatusBarRuler

        return prompt_toolkit.layout.HSplit([
            window,
            prompt_toolkit.layout.VSplit([
                WindowStatusBar(editor, editor_buffer),
                WindowStatusBarRuler(editor, window,
                                     editor_buffer.buffer),
            ], width=prompt_toolkit.layout.Dimension()),  # Ignore actual status bar width.
        ]), window

    def _get_line_prefix(self, buffer, line_number, wrap_count):
        if wrap_count > 0:
            result = []

            # Add 'breakindent' prefix.
            from ...editor import get_editor
            editor = get_editor()
            if editor.break_indent:
                line = buffer.document.lines[line_number]
                prefix = line[:len(line) - len(line.lstrip())]
                result.append(('', prefix))

            # Add softwrap mark.
            result.append(('class:soft-wrap', '...'))
            return result
        return ''

    def _get_vertical_border_char(self):
        " Return the character to be used for the vertical border. "
        return _try_char('\u2502', '|', get_app().output.encoding())

    def _create_buffer_control(self, editor_buffer):
        """
        Create a new BufferControl for a given location.
        """
        @prompt_toolkit.filters.Condition
        def preview_search():
            from ...editor import get_editor
            editor = get_editor()
            return editor.incsearch

        from ...editor import get_editor
        editor = get_editor()

        from ..reporting_processor import ReportingProcessor
        input_processors = [
            # Processor for visualising spaces. (should come before the
            # selection processor, otherwise, we won't see these spaces
            # selected.)
            prompt_toolkit.layout.processors.ConditionalProcessor(
                prompt_toolkit.layout.processors.ShowTrailingWhiteSpaceProcessor(),
                prompt_toolkit.filters.Condition(lambda: editor.display_unprintable_characters)),

            # Replace tabs by spaces.
            prompt_toolkit.layout.processors.TabsProcessor(
                tabstop=(lambda: editor.tabstop),
                char1=(
                    lambda: '|' if editor.display_unprintable_characters else ' '),
                char2=(lambda: _try_char('\u2508', '.', get_app().output.encoding())
                       if editor.display_unprintable_characters else ' '),
            ),

            # Reporting of errors, for Pyflakes.
            ReportingProcessor(editor_buffer),
            prompt_toolkit.layout.processors.HighlightSelectionProcessor(),
            prompt_toolkit.layout.processors.ConditionalProcessor(
                prompt_toolkit.layout.processors.HighlightSearchProcessor(),
                prompt_toolkit.filters.Condition(lambda: editor.highlight_search)),
            prompt_toolkit.layout.processors.ConditionalProcessor(
                prompt_toolkit.layout.processors.HighlightIncrementalSearchProcessor(),
                prompt_toolkit.filters.Condition(lambda: editor.highlight_search) & preview_search),
            prompt_toolkit.layout.processors.HighlightMatchingBracketProcessor(),
            prompt_toolkit.layout.processors.DisplayMultipleCursors(),
        ]

        from .lexer import DocumentLexer
        return prompt_toolkit.layout.BufferControl(
            lexer=DocumentLexer(editor_buffer),
            include_default_input_processors=False,
            input_processors=input_processors,
            buffer=editor_buffer.buffer,
            preview_search=preview_search,
            search_buffer_control=self.search_control,
            focus_on_click=True)
