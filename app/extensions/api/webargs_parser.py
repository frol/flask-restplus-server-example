# encoding: utf-8
"""
Webargs Parser wrapper module
-----------------------------
"""
from webargs.flaskparser import FlaskParser

from .http_exceptions import abort


class CustomWebargsParser(FlaskParser):
    """
    This custom Webargs Parser aims to overload :meth:``handle_error`` in order
    to call our custom :func:``abort`` function.

    See the following issue and the related PR for more details:
    https://github.com/sloria/webargs/issues/122
    """

    def handle_error(self, error, *args, **kwargs):
        # pylint: disable=arguments-differ
        """
        Handles errors during parsing. Aborts the current HTTP request and
        responds with a 422 error.
        """
        status_code = getattr(error, 'status_code', self.DEFAULT_VALIDATION_STATUS)
        abort(status_code, messages=error.messages)
