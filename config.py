import os


class BaseConfig(object):
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % (
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "example.db")
    )
    
    DEBUG = False

    AUTHORIZATIONS = {
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
                {
                    'scope': 'teams:read',
                    'description': "Read teams",
                },
                {
                    'scope': 'teams:write',
                    'description': "Write teams",
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

    ENABLED_MODULES = (
        'auth',

        'users',
        'teams',

        'api',
    )

    # TODO: consider if these are relevant for this project
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    CSRF_ENABLED = True


class ProductionConfig(BaseConfig):
    pass


class DevelopmentConfig(BaseConfig):
    DEBUG = True
