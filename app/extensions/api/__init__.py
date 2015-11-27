from flask import Blueprint

from .api import Api
from .http_exceptions import abort


api_v1 = Api(
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
