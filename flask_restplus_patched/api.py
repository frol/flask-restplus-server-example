from flask import jsonify
from flask_restplus import Api as OriginalApi
from werkzeug import cached_property, exceptions as http_exceptions

from .namespace import Namespace
from .swagger import Swagger


class Api(OriginalApi):

    @cached_property
    def __schema__(self):
        # The only purpose of this method is to pass custom Swagger class
        return Swagger(self).as_dict()

    def init_app(self, app):
        super(Api, self).init_app(app)
        app.errorhandler(http_exceptions.UnprocessableEntity.code)(handle_validation_error)

    def namespace(self, *args, **kwargs):
        # The only purpose of this method is to pass custom Namespace class
        _namespace = Namespace(*args, **kwargs)
        self.namespaces.append(_namespace)
        return _namespace


# Return validation errors as JSON
def handle_validation_error(err):
    exc = err.data['exc']
    return jsonify({
        'status': http_exceptions.UnprocessableEntity.code,
        'message': exc.messages
    }), http_exceptions.UnprocessableEntity.code
