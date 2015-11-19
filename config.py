import os


class BaseConfig(object):
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % (
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "example.db")
    )
    
    DEBUG = False

    # TODO: consider if these are relevant for this project
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    CSRF_ENABLED = True


class ProductionConfig(BaseConfig):
    pass


class DevelopmentConfig(BaseConfig):
    DEBUG = True
