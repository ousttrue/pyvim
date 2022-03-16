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
import pathlib
import docopt
import os
import logging
from pyvim.rc_file import run_rc_file

__all__ = (
    'run',
)


def run():
    logging.basicConfig(level=logging.DEBUG)
    a = docopt.docopt(__doc__)  # type: ignore
    locations = [pathlib.Path(x).absolute() for x in a['<location>']]
    in_tab_pages = a['-p']
    hsplit = a['-o']
    vsplit = a['-O']
    pyvimrc = a['-u']

    # Create new editor instance.
    from pyvim.editor import get_editor
    editor = get_editor()

    # Apply rc file.
    if pyvimrc:
        run_rc_file(pyvimrc)
    else:
        default_pyvimrc = os.path.expanduser('~/.pyvimrc')

        if os.path.exists(default_pyvimrc):
            run_rc_file(default_pyvimrc)

    # Load files and run.
    editor.layout()
    editor.load_initial_files(locations, in_tab_pages=in_tab_pages,
                              hsplit=hsplit, vsplit=vsplit)
    editor.run()


if __name__ == '__main__':
    run()
