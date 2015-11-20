from flask import Blueprint
#from flask.ext.restplus import Api
from flask_restplus_patched import Api, abort as restplus_abort
from werkzeug.exceptions import Unauthorized, Forbidden


API_DEFAULT_HTTP_CODE_MESSAGES = {
    Unauthorized.code: (
        "The server could not verify that you are authorized to access the "
        "URL requested. You either supplied the wrong credentials (e.g. a bad "
        "password), or your browser doesn't understand how to supply the "
        "credentials required."
    ),
    Forbidden.code: (
        "You don't have the permission to access the requested resource."
    ),
}


def abort(code, message=None, **kwargs):
    if message is None:
        message = API_DEFAULT_HTTP_CODE_MESSAGES.get(code)
    restplus_abort(code=code, message=message)



api_v1_blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api_v1 = Api(
    api_v1_blueprint,
    version='1.0',
    title="Flask-RESTplus Example API",
    description="Real-life example RESTful API server implementation using Flask-RESTplus",
)


def init_app(app, **kwargs):
    if app.debug:
        @app.route('/swaggerui/<path:path>')
        def send_swaggerui_assets(path):
            from flask import send_from_directory
            return send_from_directory('../static/', path)

    api_v1.authorizations = app.config['AUTHORIZATIONS']
    app.register_blueprint(api_v1_blueprint)
