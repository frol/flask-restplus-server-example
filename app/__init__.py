# encoding: utf-8
# pylint: disable=invalid-name
"""
DDOTS RESTful API Server application.
"""
import logging
import os

from flask import Flask, Blueprint
from flask.ext.login import LoginManager
from flask.ext.marshmallow import Marshmallow
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
marshmallow = Marshmallow()


authorizations = {
    'oauth2': {
        'type': 'oauth2',
        'scopes': [
            {
                'scope': 'users:read',
                'description': "Read users",
            },
            {
                'scope': 'users:write',
                'description': "Write users",
            },
        ],
        'grantTypes': {
            'password': {
                'tokenName': 'access_token',
            },
            # TODO: implement Implicit Grant for third-party apps
            #'implicit': {
            #    'loginEndpoint': {
            #        'url': '/auth/oauth2/authorize',
            #    },
            #    'tokenName': 'access_token',
            #},
        },
        'flow': 'password',
        'tokenUrl': '/auth/oauth2/token',
    }
}


#from flask.ext.restplus import Api, fields
from flask_restplus_patched import Api, Schema

api_v1_blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api_v1 = Api(
    api_v1_blueprint,
    version='1.0',
    title="Flask-RESTplus Example API",
    description="Real-life example RESTful API server implementation using Flask-RESTplus",
    authorizations=authorizations,
)
api = api_v1


# TODO: move this to a common/misc module
class DefaultHTTPErrorSchema(Schema):
    status = marshmallow.Integer()
    message = marshmallow.String()


def init_extensions(app):
    db.init_app(app)

    class AlembicDatabaseMigrationConfig(object):
        def __init__(self, database, directory='migrations', **kwargs):
            self.db = database
            self.directory = directory
            self.configure_args = kwargs
    app.extensions['migrate'] = AlembicDatabaseMigrationConfig(db, compare_type=True)

    login_manager.init_app(app)

    marshmallow.init_app(app)


def init_modules(app):
    from . import auth
    auth.init_app(app, login_manager)

    from . import users
    #from . import teams

    if app.debug:
        @app.route('/swaggerui/<path:path>')
        def send_swaggerui_assets(path):
            from flask import send_from_directory
            return send_from_directory('../static/', path)

    app.register_blueprint(api_v1_blueprint)
    

def create_app(debug=None, **kwargs):
    app = Flask(__name__, **kwargs)

    config = {
        'development': 'config.DevelopmentConfig',
        'testing': 'config.TestingConfig',
        'production': 'config.ProductionConfig',
        'local': 'local_config.LocalConfig',
    }
    config_name = os.getenv('FLASK_CONFIGURATION', 'production')
    app.config.from_object(config[config_name])
    if debug is not None:
        app.debug = debug

    if app.debug:
        logging.getLogger('flask_oauthlib').setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)

        # We don't need default Flask's loggers when using invoke tasks as the
        # latter set up colorful loggers.
        for handler in app.logger.handlers:
            app.logger.removeHandler(handler)

    init_extensions(app)
    init_modules(app)

    return app
