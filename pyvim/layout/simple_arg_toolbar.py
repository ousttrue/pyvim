import prompt_toolkit.layout.containers
import prompt_toolkit.layout.controls
import prompt_toolkit.filters
from prompt_toolkit.application.current import get_app


class SimpleArgToolbar(prompt_toolkit.layout.containers.ConditionalContainer):
    """
    Simple control showing the Vi repeat arg.
    """

    def __init__(self):
        def get_tokens():
            arg = get_app().key_processor.arg
            if arg is not None:
                return [('class:arg', ' %s ' % arg)]
            else:
                return []

        super(SimpleArgToolbar, self).__init__(
            prompt_toolkit.layout.containers.Window(
                prompt_toolkit.layout.controls.FormattedTextControl(get_tokens), align=prompt_toolkit.layout.containers.WindowAlign.RIGHT),
            filter=prompt_toolkit.filters.has_arg),
