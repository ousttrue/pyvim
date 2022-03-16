from typing import NamedTuple, List
import prompt_toolkit.styles


class EditorState(NamedTuple):
    current_style: prompt_toolkit.styles.BaseStyle
    show_line_numbers: bool = True
    highlight_search: bool = True
    show_ruler: bool = True
    # ':set relativenumber'
    relative_number: bool = False
    # ':set cursorcolumn'
    cursorcolumn: bool = False
    # ':set cursorline'
    cursorline: bool = False
    # ':set colorcolumn'. List of integers.
    colorcolumn: List[int] = []
