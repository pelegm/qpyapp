"""
.. errors.py

Error handlers for apps.
"""

## Framework
import qpyapp.base
import sys
import traceback
import pygments as pyg
import pygments.lexers as pyglex
import pygments.formatters as pygfrmt
pytb = pyglex.get_lexer_by_name('pytb')
term = pygfrmt.get_formatter_by_name('terminal256')


class ErrorPrinter(qpyapp.base.Component):
    _err_sep = "=" * 79 + "\n"

    def handle_error(self, app):
        exc_info = sys.exc_info()
        tb = ''.join(traceback.format_exception(*exc_info))
        msg = self._err_sep + pyg.highlight(tb, lexer=pytb, formatter=term)
        app.prompt(msg)

