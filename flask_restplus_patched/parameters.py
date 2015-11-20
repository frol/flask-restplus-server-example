import logging
from six import itervalues

from flask.ext.marshmallow import Schema, base_fields
from marshmallow import validate
from webargs import core
from webargs.flaskparser import parser as flask_parser, FlaskParser


log = logging.getLogger(__name__)


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


class Parameters(Schema):

    def __init__(self, api=None, **kwargs):
        super(Parameters, self).__init__(strict=True, **kwargs)
        self.init_api(api)

    def init_api(self, api):
        self._api = api

    def __call__(self, func, _parameters=None, _parser=None):
        if _parameters is None:
            _parameters = self.fields
        if _parser is None:
            _parser = flask_parser

        if self._api:
            func = self._api.doc(params=_parameters)(func)
        elif self._api is None:
            log.warning(
                "Parameters %r are applied to %r but documentation won't be "
                "available in Swagger spec because you haven't passed `api` "
                "instance. Pass `False` as api instance to suppress this "
                "warning.", self, func
            )

        return _parser.use_args(_parameters)(func)


class JSONParameters(Parameters):
    """
    Base JSON parameters class forcing all fields to be in ``json``/``body``.
    """

    def __init__(self, *args, **kwargs):
        super(JSONParameters, self).__init__(*args, **kwargs)
        for field in itervalues(self.fields):
            field.metadata['location'] = 'json'

    def __call__(self, func):
        # XXX: read the note to JSONListFlaskParser
        kwargs = {}
        if self.many:
            kwargs.update(dict(
                _parser=jsonlist_flask_parser,
                _parameters={
                    'body': base_fields.Nested(self, many=True, required=True, location='json')
                }
            ))
        return super(JSONParameters, self).__call__(func, **kwargs)


class PatchJSONParameters(JSONParameters):
    """
    Base parameters class for handling PATCH arguments according to RFC 6902.
    """

    # All operations described in RFC 6902
    OP_ADD = 'add'
    OP_REMOVE = 'remove'
    OP_REPLACE = 'replace'
    OP_MOVE = 'move'
    OP_COPY = 'copy'
    OP_TEST = 'test'

    # However, we use only those which make sense in RESTful API
    OPERATION_CHOICES = (
        OP_TEST,
        OP_ADD,
        OP_REMOVE,
        OP_REPLACE,
    )
    op = base_fields.String(required=True)
    
    PATH_CHOICES = None
    path = base_fields.String(required=True)
    
    value = base_fields.Raw(required=False)

    def __init__(self, *args, **kwargs):
        super(PatchJSONParameters, self).__init__(*args, many=True, **kwargs)
        self.fields['op'].validators.append(validate.OneOf(self.OPERATION_CHOICES))
        if not self.PATH_CHOICES:
            raise ValueError("%s.PATH_CHOICES has to be set" % self.__class__.__name__)
        self.fields['path'].validators.append(validate.OneOf(self.PATH_CHOICES))
