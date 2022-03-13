
import pytest

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.input import DummyInput
from pyvim.editor import Editor
from pyvim.window_arrangement import TabPage, EditorBuffer, Window


@pytest.fixture
def editor():
    return Editor(output=DummyOutput(), input=DummyInput())


@pytest.fixture
def editor_buffer(editor):
    return EditorBuffer(editor)


@pytest.fixture
def window(editor_buffer):
    return Window(editor_buffer)


@pytest.fixture
def tab_page(window):
    return TabPage(window)
