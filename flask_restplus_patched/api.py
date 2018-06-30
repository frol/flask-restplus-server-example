from flask import jsonify
from flask_restplus import Api as OriginalApi
from flask_restplus._http import HTTPStatus
from werkzeug import cached_property

from .namespace import Namespace
from .swagger import Swagger


class Api(OriginalApi):

    @cached_property
    def __schema__(self):
        # The only purpose of this method is to pass custom Swagger class
        return Swagger(self).as_dict()

    def init_app(self, app, **kwargs):
        # This solves the issue of late resources registration:
        # https://github.com/frol/flask-restplus-server-example/issues/110
        # https://github.com/noirbizarre/flask-restplus/pull/483
        self.app = app

        super(Api, self).init_app(app, **kwargs)
        app.errorhandler(HTTPStatus.UNPROCESSABLE_ENTITY.value)(handle_validation_error)

    def namespace(self, *args, **kwargs):
        # The only purpose of this method is to pass a custom Namespace class
        _namespace = Namespace(*args, **kwargs)
        self.add_namespace(_namespace)
        return _namespace


# Return validation errors as JSON
def handle_validation_error(err):
    exc = err.data['exc']
    return jsonify({
        'status': HTTPStatus.UNPROCESSABLE_ENTITY.value,
        'message': exc.messages
    }), HTTPStatus.UNPROCESSABLE_ENTITY.value
