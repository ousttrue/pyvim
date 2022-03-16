__all__ = (
    'CommandPreviewer',
)


class CommandPreviewer(object):
    """
    Already show the effect of Vi commands before enter is pressed.
    """

    def save(self):
        """
        Back up current editor state.
        """
        from pyvim.editor import get_editor
        e = get_editor()
        self._state = e.state

    def restore(self):
        """
        Focus of Vi command line lost, undo preview.
        """
        from pyvim.editor import get_editor
        e = get_editor()
        e.state = self._state

    def preview(self, input_string: str):
        """
        Show effect of current Vi command.
        """
        # First, the apply.
        self.restore()
        from pyvim.editor import get_editor
        e = get_editor()
        e.apply(input_string)
