class OpenBufferInfo(object):
    """
    Information about an open buffer, returned by
    `WindowArrangement.list_open_buffers`.
    """

    def __init__(self, index, editor_buffer, is_active, is_visible):
        self.index = index
        self.editor_buffer = editor_buffer
        self.is_active = is_active
        self.is_visible = is_visible
