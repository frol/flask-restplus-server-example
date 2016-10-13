# pylint: disable=too-few-public-methods,invalid-name,missing-docstring
import os


class BaseConfig(object):
    SECRET_KEY = 'this-really-needs-to-be-changed'

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

    SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % (os.path.join(PROJECT_ROOT, "example.db"))

    DEBUG = False

    AUTHORIZATIONS = {
        'oauth2_password': {
            'type': 'oauth2',
            'flow': 'password',
            'scopes': {},
            'tokenUrl': '/auth/oauth2/token',
        },
        # TODO: implement other grant types for third-party apps
        #'oauth2_implicit': {
        #    'type': 'oauth2',
        #    'flow': 'implicit',
        #    'scopes': {},
        #    'authorizationUrl': '/auth/oauth2/authorize',
        #},
    }

    ENABLED_MODULES = (
        'auth',

        'users',
        'teams',

        'api',
    )

    STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

    SWAGGER_UI_JSONEDITOR = True
    SWAGGER_UI_OAUTH_CLIENT_ID = 'documentation'
    SWAGGER_UI_OAUTH_REALM = "Authentication for Flask-RESTplus Example server documentation"
    SWAGGER_UI_OAUTH_APP_NAME = "Flask-RESTplus Example server documentation"

    # TODO: consider if these are relevant for this project
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    CSRF_ENABLED = True


class ProductionConfig(BaseConfig):
    SECRET_KEY = os.getenv('CLOUDSML_API_SERVER_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('CLOUDSML_API_SERVER_SQLALCHEMY_DATABASE_URI')


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True

    # Use in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
