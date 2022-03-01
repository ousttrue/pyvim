import prompt_toolkit.layout.processors
from prompt_toolkit.layout.utils import explode_text_fragments


class ReportingProcessor(prompt_toolkit.layout.processors.Processor):
    """
    Highlight all pyflakes errors on the input.
    """

    def __init__(self, editor_buffer):
        self.editor_buffer = editor_buffer

    def apply_transformation(self, transformation_input):
        fragments = transformation_input.fragments

        if self.editor_buffer.report_errors:
            for error in self.editor_buffer.report_errors:
                if error.lineno == transformation_input.lineno:
                    fragments = explode_text_fragments(fragments)
                    for i in range(error.start_column, error.end_column):
                        if i < len(fragments):
                            fragments[i] = (
                                'class:flakeserror', fragments[i][1])

        return prompt_toolkit.layout.processors.Transformation(fragments)
