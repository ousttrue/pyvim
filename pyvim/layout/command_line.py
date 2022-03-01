import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.filters
import prompt_toolkit.layout.processors
from ..commands.lexer import create_command_lexer


class CommandLine(prompt_toolkit.layout.containers.ConditionalContainer):
    """
    The editor command line. (For at the bottom of the screen.)
    """

    def __init__(self, editor):
        ui_control = prompt_toolkit.layout.controls.BufferControl(
            buffer=editor.command_buffer,
            input_processors=[
                prompt_toolkit.layout.processors.BeforeInput(':')],
            lexer=create_command_lexer())

        super(CommandLine, self).__init__(
            prompt_toolkit.layout.containers.Window(
                ui_control,
                height=1),
            filter=prompt_toolkit.filters.has_focus(editor.command_buffer))
