from typing import Tuple
import pathlib
from .editor_root import EditorRoot
from .tabs_control import TabsToolbar


def create(config_directory: pathlib.Path) -> Tuple[EditorRoot, TabsToolbar]:
    root = EditorRoot(config_directory)
    tabbar = TabsToolbar(root.window_arrangement)
    return (root, tabbar)
