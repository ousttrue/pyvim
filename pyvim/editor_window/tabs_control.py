import prompt_toolkit.layout.controls
import prompt_toolkit.mouse_events
import prompt_toolkit.layout.containers
import prompt_toolkit.filters


class TabsControl(prompt_toolkit.layout.controls.FormattedTextControl):
    """
    Displays the tabs at the top of the screen, when there is more than one
    open tab.
    """

    def __init__(self, window_arrangement):
        def location_for_tab(tab):
            return tab.active_window.editor_buffer.get_display_name(short=True)

        def create_tab_handler(index):
            " Return a mouse handler for this tab. Select the tab on click. "
            def handler(app, mouse_event):
                if mouse_event.event_type == prompt_toolkit.mouse_events.MouseEventType.MOUSE_DOWN:
                    window_arrangement.active_tab_index = index
                    from pyvim.editor import get_editor
                    editor = get_editor()
                    editor.sync_with_prompt_toolkit()
                else:
                    return NotImplemented
            return handler

        def get_tokens():
            selected_tab_index = window_arrangement.active_tab_index

            result = []
            append = result.append

            for i, tab in enumerate(window_arrangement.tab_pages):
                caption = location_for_tab(tab)
                if tab.has_unsaved_changes:
                    caption = ' + ' + caption

                handler = create_tab_handler(i)

                if i == selected_tab_index:
                    append(('class:tabbar.tab.active', ' %s ' %
                           caption, handler))
                else:
                    append(('class:tabbar.tab', ' %s ' % caption, handler))
                append(('class:tabbar', ' '))

            return result

        super(TabsControl, self).__init__(get_tokens, style='class:tabbar')


class TabsToolbar(prompt_toolkit.layout.containers.ConditionalContainer):
    def __init__(self, window_arrangement):
        super(TabsToolbar, self).__init__(
            prompt_toolkit.layout.containers.Window(
                TabsControl(window_arrangement), height=1),
            filter=prompt_toolkit.filters.Condition(lambda: len(window_arrangement.tab_pages) > 1))
