import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.filters


class WindowStatusBarRuler(prompt_toolkit.layout.containers.ConditionalContainer):
    """
    The right side of the Vim toolbar, showing the location of the cursor in
    the file, and the vectical scroll percentage.
    """

    def __init__(self, editor, buffer_window, buffer):
        def get_scroll_text():
            info = buffer_window.render_info

            if info:
                if info.full_height_visible:
                    return 'All'
                elif info.top_visible:
                    return 'Top'
                elif info.bottom_visible:
                    return 'Bot'
                else:
                    percentage = info.vertical_scroll_percentage
                    return '%2i%%' % percentage

            return ''

        def get_tokens():
            main_document = buffer.document

            return [
                ('class:cursorposition', '(%i,%i)' % (main_document.cursor_position_row + 1,
                                                      main_document.cursor_position_col + 1)),
                ('', ' - '),
                ('class:percentage', get_scroll_text()),
                ('', ' '),
            ]

        super(WindowStatusBarRuler, self).__init__(
            prompt_toolkit.layout.containers.Window(
                prompt_toolkit.layout.controls.FormattedTextControl(
                    get_tokens),
                char=' ',
                align=prompt_toolkit.layout.containers.WindowAlign.RIGHT,
                style='class:toolbar.status',
                height=1,
            ),
            filter=prompt_toolkit.filters.Condition(lambda: editor.state.show_ruler))
