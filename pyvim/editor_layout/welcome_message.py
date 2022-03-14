"""
The welcome message. This is displayed when the editor opens without any files.
"""
import pyvim
import platform
import prompt_toolkit
import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.filters


__all__ = (
    'WELCOME_MESSAGE_TOKENS',
    'WELCOME_MESSAGE_WIDTH',
    'WELCOME_MESSAGE_HEIGHT',
)

WELCOME_MESSAGE_WIDTH = 36


WELCOME_MESSAGE_TOKENS = [
    ('class:title', 'PyVim - Pure Python Vi clone\n'),
    ('', 'Still experimental\n\n'),
    ('', 'version '), ('class:version', pyvim.__version__),
    ('', ', prompt_toolkit '), ('class:version', prompt_toolkit.__version__),
    ('', '\n'),
    ('', 'by Jonathan Slenders\n\n'),
    ('', 'type :q'),
    ('class:key', '<Enter>'),
    ('', '            to exit\n'),
    ('', 'type :help'),
    ('class:key', '<Enter>'),
    ('', ' or '),
    ('class:key', '<F1>'),
    ('', ' for help\n\n'),
    ('', 'All feedback is appreciated.\n\n'),
    ('class:pythonversion', ' %s %s ' % (
        platform.python_implementation(),
        pyvim.__version__)),
]

WELCOME_MESSAGE_HEIGHT = ''.join(
    t[1] for t in WELCOME_MESSAGE_TOKENS).count('\n') + 1


class WelcomeMessageWindow(prompt_toolkit.layout.containers.ConditionalContainer):
    """
    Welcome message pop-up, which is shown during start-up when no other files
    were opened.
    """

    def __init__(self, window_arrangement):
        once_hidden = [False]  # Nonlocal

        def condition():
            # Get editor buffers
            buffers = window_arrangement.editor_buffers

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
