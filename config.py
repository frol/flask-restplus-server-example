# pylint: disable=too-few-public-methods,invalid-name,missing-docstring
import os


class BaseConfig(object):
    SECRET_KEY = 'this-really-needs-to-be-changed'

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

    # POSTGRESQL
    # DB_USER = 'user'
    # DB_PASSWORD = 'password'
    # DB_NAME = 'restplusdb'
    # DB_HOST = 'localhost'
    # DB_PORT = 5432
    # SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{password}@{host}:{port}/{name}'.format(
    #     user=DB_USER,
    #     password=DB_PASSWORD,
    #     host=DB_HOST,
    #     port=DB_PORT,
    #     name=DB_NAME,
    # )

    # SQLITE
    SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % (os.path.join(PROJECT_ROOT, "example.db"))

    DEBUG = False
    ERROR_404_HELP = False

    REVERSE_PROXY_SETUP = os.getenv('EXAMPLE_API_REVERSE_PROXY_SETUP', False)

    SQLALCHEMY_ECHO=True

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

    OAUTH2_ERROR_URIS = [('invalid_request', '/oauth2/invalid_request')]
    OAUTH2_EXPIRES_IN = {
        'authorization_code':864000,
        'implicit':          3600,
        'password':          864000,
        'client_credentials':864000
    }
    STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

    SWAGGER_UI_JSONEDITOR = True
    SWAGGER_UI_OAUTH_CLIENT_ID = 'documentation'
    SWAGGER_UI_OAUTH_REALM = "Authentication for Flask-RESTplus Example server documentation"
    SWAGGER_UI_OAUTH_APP_NAME = "Flask-RESTplus Example server documentation"

    # TODO: consider if these are relevant for this project
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    CSRF_ENABLED = True


class ProductionConfig(BaseConfig):
    SECRET_KEY = os.getenv('EXAMPLE_API_SERVER_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('EXAMPLE_API_SERVER_SQLALCHEMY_DATABASE_URI')


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True

    # Use in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
