"""
The actual layout for the renderer.
"""
from __future__ import unicode_literals
from prompt_toolkit.application.current import get_app
import prompt_toolkit.filters

from prompt_toolkit.layout import HSplit, VSplit, FloatContainer, Float, Layout
from prompt_toolkit.layout.containers import Window, ConditionalContainer, ColorColumn, ScrollOffsets
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.margins import ConditionalMargin, NumberedMargin
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import ConditionalProcessor, ShowTrailingWhiteSpaceProcessor, HighlightSelectionProcessor, HighlightSearchProcessor, HighlightIncrementalSearchProcessor, HighlightMatchingBracketProcessor, TabsProcessor, DisplayMultipleCursors
from prompt_toolkit.widgets.toolbars import SystemToolbar, SearchToolbar, ValidationToolbar, CompletionsToolbar

from ..lexer import DocumentLexer

import pyvim.window_arrangement as window_arrangement
from functools import partial

import sys

__all__ = (
    'EditorLayout',
)


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


class EditorLayout(object):
    """
    The main layout class.
    """

    def __init__(self, editor, window_arrangement: window_arrangement.WindowArrangement):
        self.editor = editor  # Back reference to editor.
        self.window_arrangement = window_arrangement

        # Mapping from (`window_arrangement.Window`, `EditorBuffer`) to a frame
        # (Layout instance).
        # We keep this as a cache in order to easily reuse the same frames when
        # the layout is updated. (We don't want to create new frames on every
        # update call, because that way, we would loose some state, like the
        # vertical scroll offset.)
        self._frames = {}

        from .welcome_message import WelcomeMessageWindow, WELCOME_MESSAGE_HEIGHT, WELCOME_MESSAGE_WIDTH
        from .buffer_list import BufferListOverlay, _bufferlist_overlay_visible
        from .message_toolbar import MessageToolbarBar

        self._fc = FloatContainer(
            content=VSplit([
                Window(BufferControl())  # Dummy window
            ]),
            floats=[
                Float(xcursor=True, ycursor=True,
                      content=CompletionsMenu(max_height=12,
                                              scroll_offset=2,
                                              extra_filter=~prompt_toolkit.filters.has_focus(editor.command_buffer))),
                Float(content=BufferListOverlay(editor), bottom=1, left=0),
                Float(bottom=1, left=0, right=0, height=1,
                      content=ConditionalContainer(
                          CompletionsToolbar(),
                          filter=prompt_toolkit.filters.has_focus(editor.command_buffer) &
                          ~_bufferlist_overlay_visible(editor) &
                          prompt_toolkit.filters.Condition(lambda: editor.show_wildmenu))),
                Float(bottom=1, left=0, right=0, height=1,
                      content=ValidationToolbar()),
                Float(bottom=1, left=0, right=0, height=1,
                      content=MessageToolbarBar(editor)),
                Float(content=WelcomeMessageWindow(window_arrangement),
                      height=WELCOME_MESSAGE_HEIGHT,
                      width=WELCOME_MESSAGE_WIDTH),
            ]
        )

        search_toolbar = SearchToolbar(
            vi_mode=True, search_buffer=editor.search_buffer)
        self.search_control = search_toolbar.control

        from .tabs_control import TabsToolbar
        from .command_line import CommandLine
        from .report_message_toolbar import ReportMessageToolbar
        from .simple_arg_toolbar import SimpleArgToolbar

        self.layout = Layout(FloatContainer(
            content=HSplit([
                TabsToolbar(editor),
                self._fc,
                CommandLine(editor),
                ReportMessageToolbar(editor),
                SystemToolbar(),
                search_toolbar,
            ]),
            floats=[
                Float(right=0, height=1, bottom=0, width=5,
                      content=SimpleArgToolbar()),
            ]
        ))

    def get_vertical_border_char(self):
        " Return the character to be used for the vertical border. "
        return _try_char('\u2502', '|', get_app().output.encoding())

    def update(self):
        """
        Update layout to match the layout as described in the
        WindowArrangement.
        """
        # Start with an empty frames list everytime, to avoid memory leaks.
        existing_frames = self._frames
        self._frames = {}

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
                return VSplit(
                    [create_layout_from_node(n) for n in node],
                    padding=1,
                    padding_char=self.get_vertical_border_char(),
                    padding_style='class:frameborder')

            if isinstance(node, window_arrangement.HSplit):
                return HSplit([create_layout_from_node(n) for n in node])

        layout = create_layout_from_node(
            self.window_arrangement.active_tab.root)
        self._fc.content = layout

    def _create_window_frame(self, editor_buffer):
        """
        Create a Window for the buffer, with underneat a status bar.
        """
        @prompt_toolkit.filters.Condition
        def wrap_lines():
            return self.editor.wrap_lines

        window = Window(
            self._create_buffer_control(editor_buffer),
            allow_scroll_beyond_bottom=True,
            scroll_offsets=ScrollOffsets(
                left=0, right=0,
                top=(lambda: self.editor.scroll_offset),
                bottom=(lambda: self.editor.scroll_offset)),
            wrap_lines=wrap_lines,
            left_margins=[ConditionalMargin(
                margin=NumberedMargin(
                    display_tildes=True,
                    relative=prompt_toolkit.filters.Condition(lambda: self.editor.relative_number)),
                filter=prompt_toolkit.filters.Condition(lambda: self.editor.show_line_numbers))],
            cursorline=prompt_toolkit.filters.Condition(
                lambda: self.editor.cursorline),
            cursorcolumn=prompt_toolkit.filters.Condition(
                lambda: self.editor.cursorcolumn),
            colorcolumns=(
                lambda: [ColorColumn(pos) for pos in self.editor.colorcolumn]),
            ignore_content_width=True,
            ignore_content_height=True,
            get_line_prefix=partial(self._get_line_prefix, editor_buffer.buffer))

        from .window_statusbar import WindowStatusBar
        from .window_statusbar_ruler import WindowStatusBarRuler

        return HSplit([
            window,
            VSplit([
                WindowStatusBar(self.editor, editor_buffer),
                WindowStatusBarRuler(self.editor, window,
                                     editor_buffer.buffer),
            ], width=Dimension()),  # Ignore actual status bar width.
        ]), window

    def _create_buffer_control(self, editor_buffer):
        """
        Create a new BufferControl for a given location.
        """
        @prompt_toolkit.filters.Condition
        def preview_search():
            return self.editor.incsearch

        from .reporting_processor import ReportingProcessor
        input_processors = [
            # Processor for visualising spaces. (should come before the
            # selection processor, otherwise, we won't see these spaces
            # selected.)
            ConditionalProcessor(
                ShowTrailingWhiteSpaceProcessor(),
                prompt_toolkit.filters.Condition(lambda: self.editor.display_unprintable_characters)),

            # Replace tabs by spaces.
            TabsProcessor(
                tabstop=(lambda: self.editor.tabstop),
                char1=(
                    lambda: '|' if self.editor.display_unprintable_characters else ' '),
                char2=(lambda: _try_char('\u2508', '.', get_app().output.encoding())
                       if self.editor.display_unprintable_characters else ' '),
            ),

            # Reporting of errors, for Pyflakes.
            ReportingProcessor(editor_buffer),
            HighlightSelectionProcessor(),
            ConditionalProcessor(
                HighlightSearchProcessor(),
                prompt_toolkit.filters.Condition(lambda: self.editor.highlight_search)),
            ConditionalProcessor(
                HighlightIncrementalSearchProcessor(),
                prompt_toolkit.filters.Condition(lambda: self.editor.highlight_search) & preview_search),
            HighlightMatchingBracketProcessor(),
            DisplayMultipleCursors(),
        ]

        return BufferControl(
            lexer=DocumentLexer(editor_buffer),
            include_default_input_processors=False,
            input_processors=input_processors,
            buffer=editor_buffer.buffer,
            preview_search=preview_search,
            search_buffer_control=self.search_control,
            focus_on_click=True)

    def _get_line_prefix(self, buffer, line_number, wrap_count):
        if wrap_count > 0:
            result = []

            # Add 'breakindent' prefix.
            if self.editor.break_indent:
                line = buffer.document.lines[line_number]
                prefix = line[:len(line) - len(line.lstrip())]
                result.append(('', prefix))

            # Add softwrap mark.
            result.append(('class:soft-wrap', '...'))
            return result
        return ''
