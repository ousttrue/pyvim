from .editor_buffer import EditorBuffer


class OpenBufferInfo(object):
    """
    Information about an open buffer, returned by
    `WindowArrangement.list_open_buffers`.
    """

    def __init__(self, index: int, editor_buffer: EditorBuffer, is_active: bool, is_visible: bool):
        self.index = index
        self.editor_buffer = editor_buffer
        self.is_active = is_active
        self.is_visible = is_visible
