import sys
from functools import partial
from prompt_toolkit.application.current import get_app
import prompt_toolkit.filters
import prompt_toolkit.layout
import prompt_toolkit.layout.processors
from .editor_buffer import EditorBuffer


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


def create_buffer_control(search_control, editor_buffer: EditorBuffer):
    """
    Create a new BufferControl for a given location.
    """
    @prompt_toolkit.filters.Condition
    def preview_search():
        from pyvim.editor import get_editor
        editor = get_editor()
        return editor.incsearch

    from pyvim.editor import get_editor
    editor = get_editor()

    from .reporting_processor import ReportingProcessor
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
            prompt_toolkit.filters.Condition(lambda: editor.state.highlight_search)),
        prompt_toolkit.layout.processors.ConditionalProcessor(
            prompt_toolkit.layout.processors.HighlightIncrementalSearchProcessor(),
            prompt_toolkit.filters.Condition(lambda: editor.state.highlight_search) & preview_search),
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
        search_buffer_control=search_control,
        focus_on_click=True)


class EditorWindow:
    def __init__(self, search_control, editor_buffer: EditorBuffer):
        """
        Create a Window for the buffer, with underneat a status bar.
        """
        @prompt_toolkit.filters.Condition
        def wrap_lines():
            from pyvim.editor import get_editor
            editor = get_editor()
            return editor.wrap_lines

        from pyvim.editor import get_editor
        editor = get_editor()

        def get_line_prefix(buffer, line_number, wrap_count):
            if wrap_count > 0:
                result = []

                # Add 'breakindent' prefix.
                from pyvim.editor import get_editor
                editor = get_editor()
                if editor.break_indent:
                    line = buffer.document.lines[line_number]
                    prefix = line[:len(line) - len(line.lstrip())]
                    result.append(('', prefix))

                # Add softwrap mark.
                result.append(('class:soft-wrap', '...'))
                return result
            return ''

        self.window = prompt_toolkit.layout.Window(
            create_buffer_control(search_control, editor_buffer),
            allow_scroll_beyond_bottom=True,
            scroll_offsets=prompt_toolkit.layout.ScrollOffsets(
                left=0, right=0,
                top=(lambda: editor.scroll_offset),
                bottom=(lambda: editor.scroll_offset)),
            wrap_lines=wrap_lines,
            left_margins=[prompt_toolkit.layout.ConditionalMargin(
                margin=prompt_toolkit.layout.NumberedMargin(
                    display_tildes=True,
                    relative=prompt_toolkit.filters.Condition(lambda: editor.state.relative_number)),
                filter=prompt_toolkit.filters.Condition(lambda: editor.state.show_line_numbers))],
            cursorline=prompt_toolkit.filters.Condition(
                lambda: editor.state.cursorline),
            cursorcolumn=prompt_toolkit.filters.Condition(
                lambda: editor.state.cursorcolumn),
            colorcolumns=(
                lambda: [prompt_toolkit.layout.ColorColumn(pos) for pos in editor.state.colorcolumn]),
            ignore_content_width=True,
            ignore_content_height=True,
            get_line_prefix=partial(get_line_prefix, editor_buffer.buffer))

        from .window_statusbar import WindowStatusBar
        from .window_statusbar_ruler import WindowStatusBarRuler

        self.container = prompt_toolkit.layout.HSplit([
            self.window,
            prompt_toolkit.layout.VSplit([
                WindowStatusBar(editor, editor_buffer),
                WindowStatusBarRuler(editor, self.window,
                                     editor_buffer.buffer),
            ], width=prompt_toolkit.layout.Dimension()),  # Ignore actual status bar width.
        ])

    def __pt_container__(self) -> prompt_toolkit.layout.Container:
        return self.container
