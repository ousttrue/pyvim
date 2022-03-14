import pathlib
import prompt_toolkit.widgets
import prompt_toolkit.history
import prompt_toolkit.buffer
import prompt_toolkit.filters


class SearchLine:
    def __init__(self, config_directory: pathlib.Path) -> None:
        search_buffer_history = prompt_toolkit.history.FileHistory(
            str(config_directory / 'search_history'))
        self.search_buffer = prompt_toolkit.buffer.Buffer(
            history=search_buffer_history,
            enable_history_search=True,
            multiline=False)
        self.has_focus = prompt_toolkit.filters.has_focus(self.search_buffer)

        self.search_toolbar = prompt_toolkit.widgets.SearchToolbar(
            vi_mode=True, search_buffer=self.search_buffer)
        self.search_control = self.search_toolbar.control

    def __pt_container__(self):
        return self.search_toolbar.__pt_container__()
