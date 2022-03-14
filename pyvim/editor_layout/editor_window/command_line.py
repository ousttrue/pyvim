import pathlib
from prompt_toolkit.application.current import get_app
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.filters
import prompt_toolkit.layout.processors
import prompt_toolkit.buffer
import prompt_toolkit.key_binding.vi_state
import prompt_toolkit.history
from ...commands.lexer import create_command_lexer


class CommandLine(prompt_toolkit.layout.containers.ConditionalContainer):
    """
    The editor command line. (For at the bottom of the screen.)
    """

    def __init__(self, config_directory: pathlib.Path):
        # Create history and search buffers.
        def handle_action(buff: prompt_toolkit.buffer.Buffer) -> bool:
            ' When enter is pressed in the Vi command line. '
            text = buff.text  # Remember: leave_command_mode resets the buffer.

            # First leave command mode. We want to make sure that the working
            # pane is focussed again before executing the command handlers.
            self.leave_command_mode(append_to_history=True)

            # Execute command.
            from ...commands.handler import handle_command
            handle_command(text)

            return False

        from ...commands.completer import create_command_completer
        commands_history = prompt_toolkit.history.FileHistory(
            str(config_directory / 'commands_history'))

        self.command_buffer = prompt_toolkit.buffer.Buffer(
            accept_handler=handle_action,
            enable_history_search=True,
            completer=create_command_completer(),
            history=commands_history,
            multiline=False)
        self.has_focus = prompt_toolkit.filters.has_focus(self.command_buffer)

        ui_control = prompt_toolkit.layout.controls.BufferControl(
            buffer=self.command_buffer,
            input_processors=[
                prompt_toolkit.layout.processors.BeforeInput(':')],
            lexer=create_command_lexer())

        super(CommandLine, self).__init__(
            prompt_toolkit.layout.containers.Window(
                ui_control,
                height=1),
            filter=prompt_toolkit.filters.has_focus(self.command_buffer))

        # Command line previewer.
        from ...commands.preview import CommandPreviewer
        self.previewer = CommandPreviewer()

        # Handle command line previews.
        # (e.g. when typing ':colorscheme blue', it should already show the
        # preview before pressing enter.)
        def preview(_):
            if get_app().layout.has_focus(self.command_buffer):
                self.previewer.preview(self.command_buffer.text)
        self.command_buffer.on_text_changed += preview

    def enter_command_mode(self):
        """
        Go into command mode.
        """
        get_app().layout.focus(self.command_buffer)
        get_app().vi_state.input_mode = prompt_toolkit.key_binding.vi_state.InputMode.INSERT

        self.previewer.save()

    def leave_command_mode(self, append_to_history=False):
        """
        Leave command mode. Focus document window again.
        """
        self.previewer.restore()

        get_app().layout.focus_last()
        get_app().vi_state.input_mode = prompt_toolkit.key_binding.vi_state.InputMode.NAVIGATION

        self.command_buffer.reset(append_to_history=append_to_history)
