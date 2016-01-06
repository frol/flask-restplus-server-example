# pylint: disable=too-few-public-methods,invalid-name,missing-docstring
import os
import tempfile


class BaseConfig(object):
    SECRET_KEY = 'this-really-needs-to-be-changed'

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

    SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % (os.path.join(PROJECT_ROOT, "example.db"))

    DEBUG = False

    AUTHORIZATIONS = {
        'oauth2_password': {
            'type': 'oauth2',
            'flow': 'password',
            'scopes': {
                'users:read': "Read users",
                'users:write': "Write users",
                'teams:read': "Read teams",
                'teams:write': "Write teams",
            },
            'tokenUrl': '/auth/oauth2/token',
        },
        # TODO: implement other grant types for third-party apps
        #'oauth2_implicit': {
        #    'type': 'oauth2',
        #    'flow': 'implicit',
        #    'scopes': {
        #        'users:read': "Read users",
        #        'users:write': "Write users",
        #        'teams:read': "Read teams",
        #        'teams:write': "Write teams",
        #    },
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

    # TODO: consider if these are relevant for this project
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    CSRF_ENABLED = True


class ProductionConfig(BaseConfig):
    pass


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True

    SQLALCHEMY_DATABASE_URI = None

    @classmethod
    def init(cls):
        cls.SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % (
            tempfile.NamedTemporaryFile(
                prefix='flask_restplus_example_server_db_',
                suffix='.db'
            ).name
        )

    @classmethod
    def destroy(cls):
        os.remove(cls.SQLALCHEMY_DATABASE_URI[len('sqlite:///'):])
