# encoding: utf-8
# pylint: disable=invalid-name,wrong-import-position
"""
Extensions setup
================
"""

from sqlalchemy_utils import force_auto_coercion, force_instant_defaults
force_auto_coercion()
force_instant_defaults()

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_login import LoginManager
login_manager = LoginManager()

from flask_marshmallow import Marshmallow
marshmallow = Marshmallow()

from . import api

from .auth import OAuth2Provider
oauth2 = OAuth2Provider()


class AlembicDatabaseMigrationConfig(object):
    """
    Helper config holder that provides missing functions of Flask-Alembic
    package since we use custom invoke tasks instead.
    """

    def __init__(self, database, directory='migrations', **kwargs):
        self.db = database
        self.directory = directory
        self.configure_args = kwargs


def init_app(app):
    """
    Application extensions initialization.
    """
    for extension in (
            db,
            login_manager,
            marshmallow,
            api,
            oauth2,
    ):
        extension.init_app(app)

    app.extensions['migrate'] = AlembicDatabaseMigrationConfig(db, compare_type=True)
