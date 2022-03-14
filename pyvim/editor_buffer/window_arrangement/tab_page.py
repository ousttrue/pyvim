from typing import Optional, Iterable, Tuple, List, TypeAlias
from ..editor_buffer.editor_buffer import EditorBuffer


class HSplit(list):
    """ Horizontal split. (This is a higher level split than
    prompt_toolkit.layout.HSplit.) """


class VSplit(list):
    """ Horizontal split. """


Split: TypeAlias = HSplit | VSplit


class Window(object):
    """
    Editor window: a window can show any open buffer.
    """

    def __init__(self, editor_buffer: EditorBuffer):
        assert isinstance(editor_buffer, EditorBuffer)
        self.editor_buffer = editor_buffer

        # The prompt_toolkit layout Window.
        self.pt_window = None

    def __repr__(self):
        return '%s(editor_buffer=%r)' % (self.__class__.__name__, self.editor_buffer)


class TabPage(object):
    """
    Tab page. Container for windows.
    """

    def __init__(self, window: Window):
        assert isinstance(window, Window)
        self.root = VSplit([window])

        # Keep track of which window is focusesd in this tab.
        self.active_window: Optional[Window] = window

    def windows(self) -> List[Window]:
        """ Return a list of all windows in this tab page. """
        return [window for _, window in self._walk_through_windows()]

    def window_count(self) -> int:
        """ The amount of windows in this tab. """
        return len(self.windows())

    def visible_editor_buffers(self) -> List[EditorBuffer]:
        """
        Return a list of visible `EditorBuffer` instances.
        """
        return [w.editor_buffer for w in self.windows()]

    def _walk_through_windows(self):
        """
        Yields (Split, Window) tuples.
        """
        def walk(split: Split) -> Iterable[Tuple[Split, Window]]:
            for c in split:
                if isinstance(c, (HSplit, VSplit)):
                    for i in walk(c):
                        yield i
                elif isinstance(c, Window):
                    yield split, c

        return walk(self.root)

    def _walk_through_splits(self):
        """
        Yields (parent_split, child_plit) tuples.
        """
        def walk(split: Split) -> Iterable[Tuple[Split, Split]]:
            for c in split:
                if isinstance(c, (HSplit, VSplit)):
                    yield split, c
                    for i in walk(c):
                        yield i

        return walk(self.root)

    def _get_active_split(self) -> Split:
        for split, window in self._walk_through_windows():
            if window == self.active_window:
                return split
        raise Exception('active_window not found. Something is wrong.')

    def _get_split_parent(self, split) -> Optional[Split]:
        for parent, child in self._walk_through_splits():
            if child == split:
                return parent

    def _split(self, split_cls: type, editor_buffer: Optional[EditorBuffer] = None):
        """
        Split horizontal or vertical.
        (when editor_buffer is None, show the current buffer there as well.)
        """
        if editor_buffer is None:
            assert(self.active_window)
            editor_buffer = self.active_window.editor_buffer
        assert(editor_buffer)

        active_split = self._get_active_split()
        index = active_split.index(self.active_window)
        new_window = Window(editor_buffer)

        if isinstance(active_split, split_cls):
            # Add new window to active split.
            active_split.insert(index, new_window)
        else:
            # Split in the other direction.
            active_split[index] = split_cls([active_split[index], new_window])

        # Focus new window.
        self.active_window = new_window

    def hsplit(self, editor_buffer: Optional[EditorBuffer] = None):
        """
        Split active window horizontally.
        """
        self._split(HSplit, editor_buffer)

    def vsplit(self, editor_buffer: Optional[EditorBuffer] = None):
        """
        Split active window vertically.
        """
        self._split(VSplit, editor_buffer)

    def show_editor_buffer(self, editor_buffer: EditorBuffer):
        """
        Open this `EditorBuffer` in the active window.
        """
        assert(self.active_window)
        assert isinstance(editor_buffer, EditorBuffer)
        self.active_window.editor_buffer = editor_buffer

    def close_editor_buffer(self, editor_buffer: EditorBuffer):
        """
        Close all the windows that have this editor buffer open.
        """
        for split, window in self._walk_through_windows():
            if window.editor_buffer == editor_buffer:
                self._close_window(window)

    def _close_window(self, window: Window):
        """
        Close this window.
        """
        if window == self.active_window:
            self.close_active_window()
        else:
            original_active_window = self.active_window
            self.close_active_window()
            self.active_window = original_active_window

    def close_active_window(self):
        """
        Close active window.
        """
        active_split = self._get_active_split()

        # First remove the active window from its split.
        index = active_split.index(self.active_window)
        del active_split[index]

        # Move focus.
        if len(active_split):
            new_active_window = active_split[max(0, index - 1)]
            while isinstance(new_active_window, (HSplit, VSplit)):
                new_active_window = new_active_window[0]
            self.active_window = new_active_window
        else:
            self.active_window = None  # No windows left.

        # When there is exactly on item left, move this back into the parent
        # split. (We don't want to keep a split with one item around -- exept
        # for the root.)
        if len(active_split) == 1 and active_split != self.root:
            parent = self._get_split_parent(active_split)
            assert(parent)
            index = parent.index(active_split)
            parent[index] = active_split[0]

    def cycle_focus(self):
        """
        Cycle through all windows.
        """
        assert(self.active_window)
        windows = self.windows()
        new_index = (windows.index(self.active_window) + 1) % len(windows)
        self.active_window = windows[new_index]

    @property
    def has_unsaved_changes(self):
        """
        True when any of the visible buffers in this tab has unsaved changes.
        """
        for w in self.windows():
            if w.editor_buffer.has_unsaved_changes:
                return True
        return False
