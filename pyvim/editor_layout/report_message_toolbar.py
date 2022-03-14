import prompt_toolkit.layout.containers
import prompt_toolkit.widgets
import prompt_toolkit.filters


class ReportMessageToolbar(prompt_toolkit.layout.containers.ConditionalContainer):
    """
    Toolbar that shows the messages, given by the reporter.
    (It shows the error message, related to the current line.)
    """

    def __init__(self, commandbuffer_has_focus):
        from pyvim.editor import get_editor
        editor = get_editor()

        def get_formatted_text():
            eb = editor.editor_layout.editor_root.window_arrangement.active_editor_buffer

            lineno = eb.buffer.document.cursor_position_row
            errors = eb.report_errors

            for e in errors:
                if e.lineno == lineno:
                    return e.formatted_text

            return []

        super(ReportMessageToolbar, self).__init__(
            prompt_toolkit.widgets.FormattedTextToolbar(get_formatted_text),
            filter=~commandbuffer_has_focus & ~prompt_toolkit.filters.is_searching & ~prompt_toolkit.filters.has_focus('system'))
