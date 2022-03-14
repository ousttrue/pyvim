from typing import Tuple
from .editor_root import EditorRoot
from .tabs_control import TabsToolbar


def create() -> Tuple[EditorRoot, TabsToolbar]:
    root = EditorRoot()
    tabbar = TabsToolbar(root.window_arrangement)
    return (root, tabbar)
