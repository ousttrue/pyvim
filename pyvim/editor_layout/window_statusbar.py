import prompt_toolkit.widgets
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.selection import SelectionType


class WindowStatusBar(prompt_toolkit.widgets.FormattedTextToolbar):
    """
    The status bar, which is shown below each window in a tab page.
    """

    def __init__(self, editor, editor_buffer):
        def get_text():
            app = get_app()

            insert_mode = app.vi_state.input_mode in (
                InputMode.INSERT, InputMode.INSERT_MULTIPLE)
            replace_mode = app.vi_state.input_mode == InputMode.REPLACE
            sel = editor_buffer.buffer.selection_state
            temp_navigation = app.vi_state.temporary_navigation_mode
            visual_line = sel is not None and sel.type == SelectionType.LINES
            visual_block = sel is not None and sel.type == SelectionType.BLOCK
            visual_char = sel is not None and sel.type == SelectionType.CHARACTERS

            def mode():
                if get_app().layout.has_focus(editor_buffer.buffer):
                    if insert_mode:
                        if temp_navigation:
                            return ' -- (insert) --'
                        elif editor.paste_mode:
                            return ' -- INSERT (paste)--'
                        else:
                            return ' -- INSERT --'
                    elif replace_mode:
                        if temp_navigation:
                            return ' -- (replace) --'
                        else:
                            return ' -- REPLACE --'
                    elif visual_block:
                        return ' -- VISUAL BLOCK --'
                    elif visual_line:
                        return ' -- VISUAL LINE --'
                    elif visual_char:
                        return ' -- VISUAL --'
                return '                     '

            def recording():
                if app.vi_state.recording_register:
                    return 'recording '
                else:
                    return ''

            return ''.join([
                ' ',
                recording(),
                (editor_buffer.location or ''),
                (' [New File]' if editor_buffer.is_new else ''),
                ('*' if editor_buffer.has_unsaved_changes else ''),
                (' '),
                mode(),
            ])
        super(WindowStatusBar, self).__init__(
            get_text,
            style='class:toolbar.status')
