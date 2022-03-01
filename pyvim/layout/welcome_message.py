import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.filters
from ..welcome_message import WELCOME_MESSAGE_TOKENS


class WelcomeMessageWindow(prompt_toolkit.layout.containers.ConditionalContainer):
    """
    Welcome message pop-up, which is shown during start-up when no other files
    were opened.
    """

    def __init__(self, editor):
        once_hidden = [False]  # Nonlocal

        def condition():
            # Get editor buffers
            buffers = editor.window_arrangement.editor_buffers

            # Only show when there is only one empty buffer, but once the
            # welcome message has been hidden, don't show it again.
            result = (len(buffers) == 1 and buffers[0].buffer.text == '' and
                      buffers[0].location is None and not once_hidden[0])
            if not result:
                once_hidden[0] = True
            return result

        super(WelcomeMessageWindow, self).__init__(
            prompt_toolkit.layout.containers.Window(
                prompt_toolkit.layout.controls.FormattedTextControl(
                    lambda: WELCOME_MESSAGE_TOKENS),
                align=prompt_toolkit.layout.containers.WindowAlign.CENTER,
                style="class:welcome"),
            filter=prompt_toolkit.filters.Condition(condition))
