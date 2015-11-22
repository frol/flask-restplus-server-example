from webargs import core
from webargs.flaskparser import FlaskParser


# XXX: It is a patched parser which surves the only purpose, support
# bulk-list-type arguments: https://github.com/sloria/webargs/issues/81
class JSONListFlaskParser(FlaskParser):

    def parse_json(self, req, name, field):
        """Pull a json list value from the request."""
        if name != 'body':
            return core.missing
        # Fail silently so that the webargs parser can handle the error
        return req.get_json(silent=True)

jsonlist_flask_parser = JSONListFlaskParser()
