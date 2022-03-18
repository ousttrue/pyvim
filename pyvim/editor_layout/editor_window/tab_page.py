from typing import Optional, Iterable, Tuple, List
from .editor_buffer import EditorBuffer


class TabNode:
    pass


class TabWindow(TabNode):
    """
    Editor window: a window can show any open buffer.
    """

    def __init__(self, editor_buffer: EditorBuffer):
        assert isinstance(editor_buffer, EditorBuffer)
        self.editor_buffer = editor_buffer

    def __repr__(self):
        return '%s(editor_buffer=%r)' % (self.__class__.__name__, self.editor_buffer)


class TabSplit(TabNode):
    def __init__(self, *window: TabWindow) -> None:
        super().__init__()
        self.children: List[TabNode] = list(window)


class TabHSplit(TabSplit):
    """ Horizontal split. (This is a higher level split than
    prompt_toolkit.layout.HSplit.) """


class TabVSplit(TabSplit):
    """ Horizontal split. """


class TabPage(object):
    """
    Tab page. Container for windows.
    """

    def __init__(self, window: TabWindow):
        self.root = TabVSplit(window)

        # Keep track of which window is focusesd in this tab.
        self._active_window: Optional[TabWindow] = window

    @property
    def active_window(self) -> TabWindow:
        assert(self._active_window)
        return self._active_window

    def windows(self) -> List[TabWindow]:
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
        def walk(split: TabSplit) -> Iterable[Tuple[TabSplit, TabWindow]]:
            for c in split.children:
                if isinstance(c, (TabHSplit, TabVSplit)):
                    for i in walk(c):
                        yield i
                elif isinstance(c, TabWindow):
                    yield split, c

        return walk(self.root)

    def _walk_through_splits(self):
        """
        Yields (parent_split, child_plit) tuples.
        """
        def walk(split: TabSplit) -> Iterable[Tuple[TabSplit, TabSplit]]:
            for c in split.children:
                if isinstance(c, (TabHSplit, TabVSplit)):
                    yield split, c
                    for i in walk(c):
                        yield i

        return walk(self.root)

    def _get_active_split(self) -> TabSplit:
        for split, window in self._walk_through_windows():
            if window == self._active_window:
                return split
        raise Exception('active_window not found. Something is wrong.')

    def _get_split_parent(self, split) -> Optional[TabSplit]:
        for parent, child in self._walk_through_splits():
            if child == split:
                return parent

    def _split(self, split_cls: type, editor_buffer: Optional[EditorBuffer] = None):
        """
        Split horizontal or vertical.
        (when editor_buffer is None, show the current buffer there as well.)
        """
        assert(self._active_window)
        if editor_buffer is None:
            editor_buffer = self._active_window.editor_buffer
        assert(editor_buffer)

        active_split = self._get_active_split()
        index = active_split.children.index(self._active_window)
        new_window = TabWindow(editor_buffer)

        if isinstance(active_split, split_cls):
            # Add new window to active split.
            active_split.children.insert(index, new_window)
        else:
            # Split in the other direction.
            active_split.children[index] = split_cls(
                [active_split.children[index], new_window])

        # Focus new window.
        self._active_window = new_window

    def hsplit(self, editor_buffer: Optional[EditorBuffer] = None):
        """
        Split active window horizontally.
        """
        self._split(TabHSplit, editor_buffer)

    def vsplit(self, editor_buffer: Optional[EditorBuffer] = None):
        """
        Split active window vertically.
        """
        self._split(TabVSplit, editor_buffer)

    def show_editor_buffer(self, editor_buffer: EditorBuffer):
        """
        Open this `EditorBuffer` in the active window.
        """
        assert(self._active_window)
        assert isinstance(editor_buffer, EditorBuffer)
        self._active_window.editor_buffer = editor_buffer

    def close_editor_buffer(self, editor_buffer: EditorBuffer):
        """
        Close all the windows that have this editor buffer open.
        """
        for split, window in self._walk_through_windows():
            if window.editor_buffer == editor_buffer:
                self._close_window(window)

    def _close_window(self, window: TabWindow):
        """
        Close this window.
        """
        if window == self._active_window:
            self.close_active_window()
        else:
            original_active_window = self._active_window
            self.close_active_window()
            self._active_window = original_active_window

    def close_active_window(self):
        """
        Close active window.
        """
        active_split = self._get_active_split()

        # First remove the active window from its split.
        assert(self._active_window)
        index = active_split.children.index(self._active_window)
        del active_split.children[index]

        # Move focus.
        if len(active_split.children):
            new_active_window = active_split.children[max(0, index - 1)]
            while isinstance(new_active_window, (TabHSplit, TabVSplit)):
                new_active_window = new_active_window.children[0]
            assert(isinstance(new_active_window, TabWindow))
            self._active_window = new_active_window
        else:
            self._active_window = None  # No windows left.

        # When there is exactly on item left, move this back into the parent
        # split. (We don't want to keep a split with one item around -- exept
        # for the root.)
        if len(active_split.children) == 1 and active_split != self.root:
            parent = self._get_split_parent(active_split)
            assert(parent)
            index = parent.children.index(active_split)
            parent.children[index] = active_split.children[0]

    def cycle_focus(self):
        """
        Cycle through all windows.
        """
        assert(self._active_window)
        windows = self.windows()
        new_index = (windows.index(self._active_window) + 1) % len(windows)
        self._active_window = windows[new_index]

    @property
    def has_unsaved_changes(self):
        """
        True when any of the visible buffers in this tab has unsaved changes.
        """
        for w in self.windows():
            if w.editor_buffer.has_unsaved_changes:
                return True
        return False
