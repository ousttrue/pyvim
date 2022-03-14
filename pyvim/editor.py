"""
The main editor class.

Usage::

    files_to_edit = ['file1.txt', 'file2.py']
    e = Editor(files_to_edit)
    e.run()  # Runs the event loop, starts interaction.
"""
from typing import Optional
import pathlib
import pygments.util
import prompt_toolkit.application
import prompt_toolkit.buffer
import prompt_toolkit.enums
import prompt_toolkit.filters
import prompt_toolkit.history
import prompt_toolkit.key_binding
import prompt_toolkit.key_binding.vi_state
import prompt_toolkit.styles
import prompt_toolkit.input
import prompt_toolkit.output
import prompt_toolkit.layout
import prompt_toolkit.cursor_shapes
from .commands.command_line import CommandLine


class _Editor(object):
    """
    The main class. Containing the whole editor.
    """

    def __init__(self):
        self.input: Optional[prompt_toolkit.input.Input] = None
        self.output: Optional[prompt_toolkit.output.Output] = None

        # Vi options.
        self.show_line_numbers = True
        self.highlight_search = True
        self.paste_mode = False
        self.show_ruler = True
        self.show_wildmenu = True
        self.expand_tab = True  # Insect spaces instead of tab characters.
        self.tabstop = 4  # Number of spaces that a tab character represents.
        self.incsearch = True  # Show matches while typing search string.
        self.ignore_case = False  # Ignore case while searching.
        self.enable_mouse_support = True
        self.display_unprintable_characters = True  # ':set list'
        self.enable_jedi = True  # ':set jedi', for Python Jedi completion.
        self.scroll_offset = 0  # ':set scrolloff'
        self.relative_number = False  # ':set relativenumber'
        self.wrap_lines = True  # ':set wrap'
        self.break_indent = False  # ':set breakindent'
        self.cursorline = False  # ':set cursorline'
        self.cursorcolumn = False  # ':set cursorcolumn'
        self.colorcolumn = []  # ':set colorcolumn'. List of integers.

        self.message = None

        # Load styles. (Mapping from name to Style class.)
        from .style import generate_built_in_styles, get_editor_style_by_name
        self.styles = generate_built_in_styles()
        self.current_style = get_editor_style_by_name('vim')

        # I/O backends.
        from .io import FileIO, DirectoryIO, HttpIO, GZipFileIO
        self.io_backends = [
            DirectoryIO(),
            HttpIO(),
            GZipFileIO(),  # Should come before FileIO.
            FileIO(),
        ]

        # Create key bindings registry.
        self.key_bindings = prompt_toolkit.key_binding.KeyBindings()

    def layout(self):
        # Ensure config directory exists.
        config_directory = pathlib.Path('~/.pyvim')
        self.config_directory = config_directory.absolute()
        if not self.config_directory.exists():
            self.config_directory.mkdir(parents=True)

        search_buffer_history = prompt_toolkit.history.FileHistory(
            str(self.config_directory / 'search_history'))
        self.search_buffer = prompt_toolkit.buffer.Buffer(
            history=search_buffer_history,
            enable_history_search=True,
            multiline=False)

        # Create layout and CommandLineInterface instance.
        from .editor_layout import EditorLayout
        self.editor_layout = EditorLayout(self.config_directory)

        # Create Application.
        self.application = prompt_toolkit.application.Application(
            input=self.input,
            output=self.output,
            editing_mode=prompt_toolkit.enums.EditingMode.VI,
            layout=prompt_toolkit.layout.Layout(self.editor_layout),
            key_bindings=self.key_bindings,
            style=prompt_toolkit.styles.DynamicStyle(
                lambda: self.current_style),
            paste_mode=prompt_toolkit.filters.Condition(
                lambda: self.paste_mode),
            #            ignore_case=Condition(lambda: self.ignore_case),  # TODO
            include_default_pygments_style=False,
            mouse_support=prompt_toolkit.filters.Condition(
                lambda: self.enable_mouse_support),
            full_screen=True,
            enable_page_navigation_bindings=True,
            color_depth=prompt_toolkit.output.color_depth.ColorDepth.DEPTH_8_BIT,
            cursor=prompt_toolkit.cursor_shapes.CursorShape.BLOCK,
        )

        # Hide message when a key is pressed.

        def key_pressed(_):
            self.message = None
        self.application.key_processor.before_key_press += key_pressed

        self.last_substitute_text = ''

        from .key_bindings import create_key_bindings
        create_key_bindings()

    def load_initial_files(self, locations, in_tab_pages=False, hsplit=False, vsplit=False):
        """
        Load a list of files.
        """
        assert in_tab_pages + hsplit + vsplit <= 1  # Max one of these options.

        # When no files were given, open at least one empty buffer.
        locations2 = locations or [None]

        # First file
        self.editor_layout.editor_root.window_arrangement.open_buffer(
            locations2[0])

        for f in locations2[1:]:
            if in_tab_pages:
                self.editor_layout.editor_root.window_arrangement.create_tab(f)
            elif hsplit:
                self.editor_layout.editor_root.window_arrangement.hsplit(
                    location=f)
            elif vsplit:
                self.editor_layout.editor_root.window_arrangement.vsplit(
                    location=f)
            else:
                self.editor_layout.editor_root.window_arrangement.open_buffer(
                    f)

        self.editor_layout.editor_root.window_arrangement.active_tab_index = 0

        if locations and len(locations) > 1:
            self.show_message('%i files loaded.' % len(locations))

    @property
    def current_editor_buffer(self):
        """
        Return the `EditorBuffer` that is currently active.
        """
        current_buffer = self.application.current_buffer

        # Find/return the EditorBuffer with this name.
        for b in self.editor_layout.editor_root.window_arrangement.editor_buffers:
            if b.buffer == current_buffer:
                return b

    @property
    def add_key_binding(self):
        """
        Shortcut for adding new key bindings.
        (Mostly useful for a pyvimrc file, that receives this Editor instance
        as input.)
        """
        return self.key_bindings.add

    def show_message(self, message):
        """
        Set a warning message. The layout will render it as a "pop-up" at the
        bottom.
        """
        self.message = message

    def use_colorscheme(self, name='default'):
        """
        Apply new colorscheme. (By name.)
        """
        try:
            from .style import get_editor_style_by_name
            self.current_style = get_editor_style_by_name(name)
        except pygments.util.ClassNotFound:
            pass

    def sync_with_prompt_toolkit(self):
        """
        Update the prompt-toolkit Layout and FocusStack.
        """
        # After executing a command, make sure that the layout of
        # prompt-toolkit matches our WindowArrangement.
        self.editor_layout.editor_root.update()

        # Make sure that the focus stack of prompt-toolkit has the current
        # page.
        window = self.editor_layout.editor_root.window_arrangement.active_pt_window
        if window:
            self.application.layout.focus(window)

    def show_help(self):
        """
        Show help in new window.
        """
        from .help import HELP_TEXT
        self.editor_layout.editor_root.window_arrangement.hsplit(
            text=HELP_TEXT)
        self.sync_with_prompt_toolkit()  # Show new window.

    def run(self):
        """
        Run the event loop for the interface.
        This starts the interaction.
        """
        # Make sure everything is in sync, before starting.
        self.sync_with_prompt_toolkit()

        def pre_run():
            # Start in navigation mode.
            self.application.vi_state.input_mode = prompt_toolkit.key_binding.vi_state.InputMode.NAVIGATION

        # Run eventloop of prompt_toolkit.
        self.application.run(pre_run=pre_run)

    @property
    def commandline(self) -> CommandLine:
        return self.editor_layout.editor_root.commandline

    @property
    def command_buffer(self) -> prompt_toolkit.buffer.Buffer:
        return self.commandline.command_buffer


EDITOR = _Editor()


def get_editor() -> _Editor:
    return EDITOR
