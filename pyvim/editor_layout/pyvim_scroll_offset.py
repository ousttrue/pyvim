import prompt_toolkit.layout.containers


class PyvimScrollOffsets(prompt_toolkit.layout.containers.ScrollOffsets):
    def __init__(self, editor):
        self.editor = editor
        self._left = 0
        self._right = 0

    @property
    def top(self):
        return self.editor.scroll_offset

    @property
    def bottom(self):
        return self.editor.scroll_offset
