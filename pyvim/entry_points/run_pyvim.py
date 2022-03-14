#!/usr/bin/env python
"""
pyvim: Pure Python Vim clone.
Usage:
    pyvim [-p] [-o] [-O] [-u <pyvimrc>] [<location>...]

Options:
    -p           : Open files in tab pages.
    -o           : Split horizontally.
    -O           : Split vertically.
    -u <pyvimrc> : Use this .pyvimrc file instead.
"""
import docopt
import os

from pyvim.editor import get_editor
from pyvim.rc_file import run_rc_file

__all__ = (
    'run',
)


def run():
    a = docopt.docopt(__doc__)  # type: ignore
    locations = a['<location>']
    in_tab_pages = a['-p']
    hsplit = a['-o']
    vsplit = a['-O']
    pyvimrc = a['-u']

    # Create new editor instance.
    editor = get_editor()

    # Apply rc file.
    if pyvimrc:
        run_rc_file(pyvimrc)
    else:
        default_pyvimrc = os.path.expanduser('~/.pyvimrc')

        if os.path.exists(default_pyvimrc):
            run_rc_file(default_pyvimrc)

    # Load files and run.
    editor.load_initial_files(locations, in_tab_pages=in_tab_pages,
                              hsplit=hsplit, vsplit=vsplit)
    editor.run()


if __name__ == '__main__':
    run()
