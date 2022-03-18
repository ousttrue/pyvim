import prompt_toolkit.layout.containers
import prompt_toolkit.widgets
import prompt_toolkit.filters


class MessageToolbarBar(prompt_toolkit.layout.containers.ConditionalContainer):
    """
    Pop-up (at the bottom) for showing error/status messages.
    """

    def __init__(self, editor):
        def get_tokens():
            if editor.message:
                return [('class:message', editor.message)]
            else:
                return []

        super(MessageToolbarBar, self).__init__(
            prompt_toolkit.widgets.FormattedTextToolbar(get_tokens),
            filter=prompt_toolkit.filters.Condition(lambda: editor.message is not None))
