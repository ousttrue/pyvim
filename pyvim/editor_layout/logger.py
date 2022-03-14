from typing import NamedTuple, List
import logging
import prompt_toolkit.layout
import prompt_toolkit.formatted_text
from prompt_toolkit.application.current import get_app

NL = ('', '\n')


class LoggerWindow(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.logs: prompt_toolkit.formatted_text.StyleAndTextTuples = []
        self.control = prompt_toolkit.layout.FormattedTextControl(
            lambda: self.logs)
        self.container = prompt_toolkit.layout.Window(
            self.control, height=8)

        # set root logger
        self.setFormatter(logging.Formatter(
            '%(filename)s:%(levelno)s: %(message)s'))
        logging.getLogger().handlers = [self]
        logging.info('start')

    def __pt_container__(self) -> prompt_toolkit.layout.Container:
        return self.container

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)

        match record.levelno:
            case logging.DEBUG:
                self.logs.append(('#AAAAAA', '[DEBUG]'))
            case logging.INFO:
                self.logs.append(('#FFFFFF bg:#888888', '[INFO ]'))
            case logging.WARN:
                self.logs.append(('#FFFFFF bg:#996600', '[WARN ]'))
            case logging.ERROR:
                self.logs.append(('#FFFFFF bg:#990000', '[ERROR]'))
            case _:
                raise NotImplementedError()
        self.logs.append(('', msg))
        self.logs.append(NL)
        while self.get_line_count() > 8:
            self.remove_line(0)
        get_app().invalidate()

    def write(self, m):
        pass

    def get_line_count(self):
        return len([x for x in self.logs if x == NL])

    def remove_line(self, index):
        logs = []
        i = 0
        for x in self.logs:
            if i != index:
                logs.append(x)
            if x == NL:
                i += 1
        self.logs = logs
