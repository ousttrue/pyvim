import re
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.filters
from prompt_toolkit.application.current import get_app


def _bufferlist_overlay_visible(editor):
    """
    True when the buffer list overlay should be displayed.
    (This is when someone starts typing ':b' or ':buffer' in the command line.)
    """
    @prompt_toolkit.filters.Condition
    def overlay_is_visible():
        app = get_app()

        text = editor.command_buffer.text.lstrip()
        return app.layout.has_focus(editor.command_buffer) and (
            any(text.startswith(p) for p in ['b ', 'b! ', 'buffer', 'buffer!']))
    return overlay_is_visible


class BufferListOverlay(prompt_toolkit.layout.containers.ConditionalContainer):
    """
    Floating window that shows the list of buffers when we are typing ':b'
    inside the vim command line.
    """

    def __init__(self, editor):
        def highlight_location(location, search_string, default_token):
            """
            Return a tokenlist with the `search_string` highlighted.
            """
            result = [(default_token, c) for c in location]

            # Replace token of matching positions.
            for m in re.finditer(re.escape(search_string), location):
                for i in range(m.start(), m.end()):
                    result[i] = ('class:searchmatch', result[i][1])

            if location == search_string:
                result[0] = (result[0][0] +
                             ' [SetCursorPosition]', result[0][1])

            return result

        def get_tokens():
            wa = editor.window_arrangement
            buffer_infos = wa.list_open_buffers()

            # Filter infos according to typed text.
            input_params = editor.command_buffer.text.lstrip().split(None, 1)
            search_string = input_params[1] if len(input_params) > 1 else ''

            if search_string:
                def matches(info):
                    """
                    True when we should show this entry.
                    """
                    # When the input appears in the location.
                    if input_params[1] in (info.editor_buffer.location or ''):
                        return True

                    # When the input matches this buffer his index number.
                    if input_params[1] in str(info.index):
                        return True

                    # When this entry is part of the current completions list.
                    b = editor.command_buffer

                    if b.complete_state and any(info.editor_buffer.location in c.display
                                                for c in b.complete_state.completions
                                                if info.editor_buffer.location is not None):
                        return True

                    return False

                buffer_infos = [info for info in buffer_infos if matches(info)]

            # Render output.
            if len(buffer_infos) == 0:
                return [('', ' No match found. ')]
            else:
                result = []

                # Create title.
                result.append(('', '  '))
                result.append(('class:title', 'Open buffers\n'))

                # Get length of longest location
                max_location_len = max(
                    len(info.editor_buffer.get_display_name()) for info in buffer_infos)

                # Show info for each buffer.
                for info in buffer_infos:
                    eb = info.editor_buffer
                    char = '%' if info.is_active else ' '
                    char2 = 'a' if info.is_visible else ' '
                    char3 = ' + ' if info.editor_buffer.has_unsaved_changes else '   '
                    t = 'class:active' if info.is_active else ''

                    result.extend([
                        ('', ' '),
                        (t, '%3i ' % info.index),
                        (t, '%s' % char),
                        (t, '%s ' % char2),
                        (t, '%s ' % char3),
                    ])
                    result.extend(highlight_location(
                        eb.get_display_name(), search_string, t))
                    result.extend([
                        (t, ' ' * (max_location_len - len(eb.get_display_name()))),
                        (t + ' class:lineno', '  line %i' %
                         (eb.buffer.document.cursor_position_row + 1)),
                        (t, ' \n')
                    ])
                return result

        super(BufferListOverlay, self).__init__(
            prompt_toolkit.layout.containers.Window(prompt_toolkit.layout.controls.FormattedTextControl(get_tokens),
                                                    style='class:bufferlist',
                                                    scroll_offsets=prompt_toolkit.layout.containers.ScrollOffsets(top=1, bottom=1)),
            filter=_bufferlist_overlay_visible(editor))
