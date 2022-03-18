"""
Window arrangement.

This contains the data structure for the tab pages with their windows and
buffers. It's not the same as a `prompt-toolkit` layout. The latter directly
represents the rendering, while this is more specific for the editor itself.
"""
from typing import List, Optional, Dict, Union
import pathlib
from six import string_types
from prompt_toolkit.application.current import get_app
import prompt_toolkit.layout
from .editor_buffer import EditorBuffer
from .openbuffer_info import OpenBufferInfo
from . import tab_page
from .editor_window import EditorWindow, _try_char

__all__ = (
    'WindowArrangement',
)


class WindowArrangement(object):
    '''
    buffers = [
        buffer1
        buffer2
    ]

    tab
      tab1
        root
          window1-1 -> buffer1
          window1-2 -> buffer2
      tab2
        window2-1 -> buffer1 

    Dict[window, buffer]

    active path: (tabN, v, h, w)
    '''

    def __init__(self, config_directory: pathlib.Path):
        self.tab_pages: List[tab_page.TabPage] = []
        self.active_tab_index: Optional[int] = None
        self.editor_buffers: List[EditorBuffer] = []
        # Mapping from (`window_arrangement.Window`, `EditorBuffer`) to a frame
        # (Layout instance).
        # We keep this as a cache in order to easily reuse the same frames when
        # the layout is updated. (We don't want to create new frames on every
        # update call, because that way, we would loose some state, like the
        # vertical scroll offset.)
        self._frames: Dict[EditorBuffer, EditorWindow] = {}

        self.container = prompt_toolkit.layout.VSplit([
            prompt_toolkit.layout.Window(
                prompt_toolkit.layout.BufferControl())  # Dummy window
        ])

        from .searchline import SearchLine
        self.searchline = SearchLine(config_directory)

    def __pt_container__(self) -> prompt_toolkit.layout.Container:
        return self.container

    @property
    def active_tab(self) -> tab_page.TabPage:
        """ The active TabPage or None. """
        if self.active_tab_index is not None:
            return self.tab_pages[self.active_tab_index]
        raise RuntimeError()

    @property
    def active_window(self) -> tab_page.TabWindow:
        return self.active_tab.active_window

    @property
    def active_editor_buffer(self) -> EditorBuffer:
        """ The active EditorBuffer or None. """
        return self.active_window.editor_buffer

    def get_editor_buffer_for_location(self, location: pathlib.Path):
        """
        Return the `EditorBuffer` for this location.
        When this file was not yet loaded, return None
        """
        for eb in self.editor_buffers:
            if eb.location == location:
                return eb

    def close_window(self):
        """
        Close active window of active tab.
        """
        self.active_tab.close_active_window()

        # Clean up buffers.
        self._auto_close_new_empty_buffers()

    def close_tab(self):
        """
        Close active tab.
        """
        assert(isinstance(self.active_tab_index, int))
        if len(self.tab_pages) > 1:  # Cannot close last tab.
            del self.tab_pages[self.active_tab_index]
            self.active_tab_index = max(0, self.active_tab_index - 1)

        # Clean up buffers.
        self._auto_close_new_empty_buffers()

    def hsplit(self, location: Optional[pathlib.Path] = None, new=False, text=None):
        """ Split horizontally. """
        assert location is None or text is None or new is False  # Don't pass two of them.

        if location or text or new:
            editor_buffer = self._get_or_create_editor_buffer(
                location=location, text=text)
        else:
            editor_buffer = None
        self.active_tab.hsplit(editor_buffer)

    def vsplit(self, location: Optional[pathlib.Path] = None, new=False, text=None):
        """ Split vertically. """
        assert location is None or text is None or new is False  # Don't pass two of them.

        if location or text or new:
            editor_buffer = self._get_or_create_editor_buffer(
                location=location, text=text)
        else:
            editor_buffer = None
        self.active_tab.vsplit(editor_buffer)

    def keep_only_current_window(self):
        """
        Close all other windows, except the current one.
        """
        self.tab_pages = [tab_page.TabPage(self.active_window)]
        self.active_tab_index = 0

    def cycle_focus(self):
        """ Focus next visible window. """
        self.active_tab.cycle_focus()

    def show_editor_buffer(self, editor_buffer):
        """
        Show this EditorBuffer in the current window.
        """
        self.active_tab.show_editor_buffer(editor_buffer)

        # Clean up buffers.
        self._auto_close_new_empty_buffers()

    def go_to_next_buffer(self, _previous=False):
        """
        Open next buffer in active window.
        """
        if self.active_editor_buffer:
            # Find the active opened buffer.
            index = self.editor_buffers.index(self.active_editor_buffer)

            # Get index of new buffer.
            if _previous:
                new_index = (len(self.editor_buffers) + index -
                             1) % len(self.editor_buffers)
            else:
                new_index = (index + 1) % len(self.editor_buffers)

            # Open new buffer in active tab.
            self.active_tab.show_editor_buffer(self.editor_buffers[new_index])

            # Clean up buffers.
            self._auto_close_new_empty_buffers()

    def go_to_previous_buffer(self):
        """
        Open the previous buffer in the active window.
        """
        self.go_to_next_buffer(_previous=True)

    def go_to_next_tab(self):
        """
        Focus the next tab.
        """
        assert(isinstance(self.active_tab_index, int))
        self.active_tab_index = (
            self.active_tab_index + 1) % len(self.tab_pages)

    def go_to_previous_tab(self):
        """
        Focus the previous tab.
        """
        assert(isinstance(self.active_tab_index, int))
        self.active_tab_index = (self.active_tab_index - 1 +
                                 len(self.tab_pages)) % len(self.tab_pages)

    def go_to_buffer(self, buffer_name):
        """
        Go to one of the open buffers.
        """
        assert isinstance(buffer_name, string_types)

        for i, eb in enumerate(self.editor_buffers):
            if (eb.location == buffer_name or
                    (buffer_name.isdigit() and int(buffer_name) == i)):
                self.show_editor_buffer(eb)
                break

    def _add_editor_buffer(self, editor_buffer, show_in_current_window=False):
        """
        Insert this new buffer in the list of buffers, right after the active
        one.
        """
        assert isinstance(
            editor_buffer, EditorBuffer) and editor_buffer not in self.editor_buffers

        # Add to list of EditorBuffers
        try:
            eb = self.active_editor_buffer
            # Append right after the currently active one.
            try:
                index = self.editor_buffers.index(eb)
            except ValueError:
                index = 0
            self.editor_buffers.insert(index, editor_buffer)
        except:
            self.editor_buffers.append(editor_buffer)

        # When there are no tabs/windows yet, create one for this buffer.
        if self.tab_pages == []:
            self.tab_pages.append(tab_page.TabPage(
                tab_page.TabWindow(editor_buffer)))
            self.active_tab_index = 0

        # To be shown?
        if show_in_current_window and self.active_tab:
            self.active_tab.show_editor_buffer(editor_buffer)

        # Start reporter.
        editor_buffer.run_reporter()

    def _get_or_create_editor_buffer(self, location: Optional[pathlib.Path] = None, text=None):
        """
        Given a location, return the `EditorBuffer` instance that we have if
        the file is already open, or create a new one.

        When location is None, this creates a new buffer.
        """
        # assert location is None or text is None  # Don't pass two of them.
        # assert location is None or isinstance(location, pathlib.Path)
        match location:
            case pathlib.Path():
                # When a location is given, first look whether the file was already
                # opened.
                eb = self.get_editor_buffer_for_location(location)

                # Not found? Create one.
                if eb is None:
                    # Create and add EditorBuffer
                    eb = EditorBuffer(location)
                    self._add_editor_buffer(eb)

                    return eb
                else:
                    # Found! Return it.
                    return eb

            case None:
                # Create and add an empty EditorBuffer
                eb = EditorBuffer(text=text)
                self._add_editor_buffer(eb)

                return eb

            case _:
                raise RuntimeError()

    def open_buffer(self, location: Optional[pathlib.Path] = None, show_in_current_window=False):
        """
        Open/create a file, load it, and show it in a new buffer.
        """
        eb = self._get_or_create_editor_buffer(location)

        if show_in_current_window:
            self.show_editor_buffer(eb)

    def _auto_close_new_empty_buffers(self):
        """
        When there are new, empty buffers open. (Like, created when the editor
        starts without any files.) These can be removed at the point when there
        is no more window showing them.

        This should be called every time when a window is closed, or when the
        content of a window is replcaed by something new.
        """
        # Get all visible EditorBuffers
        ebs = set()
        for t in self.tab_pages:
            ebs |= set(t.visible_editor_buffers())

        # Remove empty/new buffers that are hidden.
        for eb in self.editor_buffers[:]:
            if eb.is_new and not eb.location and eb not in ebs and eb.buffer.text == '':
                self.editor_buffers.remove(eb)

    def close_buffer(self):
        """
        Close current buffer. When there are other windows showing the same
        buffer, they are closed as well. When no windows are left, the previous
        buffer or an empty buffer is shown.
        """
        assert(isinstance(self.active_tab_index, int))
        eb = self.active_editor_buffer

        # Remove this buffer.
        index = self.editor_buffers.index(eb)
        self.editor_buffers.remove(eb)

        # Close the active window.
        self.active_tab.close_active_window()

        # Close all the windows that still have this buffer open.
        for i, t in enumerate(self.tab_pages[:]):
            t.close_editor_buffer(eb)

            # Remove tab when there are no windows left.
            if t.window_count() == 0:
                self.tab_pages.remove(t)

                if i >= self.active_tab_index:
                    self.active_tab_index = max(0, self.active_tab_index - 1)

        # When there are no windows/tabs left, create a new tab.
        if len(self.tab_pages) == 0:
            self.active_tab_index = None

            if len(self.editor_buffers) > 0:
                # Open the previous buffer.
                new_index = (len(self.editor_buffers) + index -
                             1) % len(self.editor_buffers)
                eb = self.editor_buffers[new_index]

                # Create a window for this buffer.
                self.tab_pages.append(tab_page.TabPage(tab_page.TabWindow(eb)))
                self.active_tab_index = 0
            else:
                # Create a new buffer. (This will also create the window
                # automatically.)
                eb = self._get_or_create_editor_buffer()

    def create_tab(self, location=None):
        """
        Create a new tab page.
        """
        assert(isinstance(self.active_tab_index, int))
        eb = self._get_or_create_editor_buffer(location)

        self.tab_pages.insert(self.active_tab_index + 1,
                              tab_page.TabPage(tab_page.TabWindow(eb)))
        self.active_tab_index += 1

    def list_open_buffers(self) -> List[OpenBufferInfo]:
        """
        Return a `OpenBufferInfo` list that gives information about the
        open buffers.
        """
        active_eb = self.active_editor_buffer
        visible_ebs = self.active_tab.visible_editor_buffers()

        def make_info(i, eb):
            return OpenBufferInfo(
                index=i,
                editor_buffer=eb,
                is_active=(eb == active_eb),
                is_visible=(eb in visible_ebs))

        return [make_info(i, eb) for i, eb in enumerate(self.editor_buffers)]

    def get_window(self, eb: EditorBuffer) -> prompt_toolkit.layout.Window:
        return self._frames[eb].window

    def update(self):
        """
        Update layout to match the layout as described in the
        WindowArrangement.
        """

        # Start with an empty frames list everytime, to avoid memory leaks.
        existing_frames = self._frames
        self._frames = {}

        def create_layout_from_node(node) -> Union[prompt_toolkit.layout.containers.Window, prompt_toolkit.layout.containers.HSplit, prompt_toolkit.layout.containers.VSplit]:
            from . import tab_page
            if isinstance(node, tab_page.TabWindow):
                # Create frame for Window, or reuse it, if we had one already.
                editor_window = existing_frames.get(node.editor_buffer)
                if not editor_window:
                    editor_window = EditorWindow(
                        self.searchline.search_control, node.editor_buffer)

                self._frames[node.editor_buffer] = editor_window
                return editor_window.window

            if isinstance(node, tab_page.TabVSplit):
                def get_vertical_border_char():
                    " Return the character to be used for the vertical border. "
                    return _try_char('\u2502', '|', get_app().output.encoding())

                return prompt_toolkit.layout.VSplit(
                    [create_layout_from_node(n) for n in node.children],
                    padding=1,
                    padding_char=get_vertical_border_char(),
                    padding_style='class:frameborder')

            if isinstance(node, tab_page.TabHSplit):
                return prompt_toolkit.layout.HSplit([create_layout_from_node(n) for n in node.children])

            raise RuntimeError()

        assert(self.active_tab)
        self.container.children = [create_layout_from_node(
            self.active_tab.root)]
