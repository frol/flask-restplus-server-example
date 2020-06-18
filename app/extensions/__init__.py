# -*- coding: utf-8 -*-
# pylint: disable=invalid-name,wrong-import-position,wrong-import-order
"""
Extensions setup
================

Extensions provide access to common resources of the application.

Please, put new extension instantiations and initializations here.
"""
from .logging import Logging

logging = Logging()

from flask_cors import CORS  # NOQA

cross_origin_resource_sharing = CORS()

from .flask_sqlalchemy import SQLAlchemy  # NOQA
from sqlalchemy.ext import mutable  # NOQA
from sqlalchemy.types import TypeDecorator, CHAR  # NOQA
from sqlalchemy.dialects.postgresql import UUID  # NOQA
from sqlalchemy_utils import types as column_types, Timestamp  # NOQA

import uuid  # NOQA

import json  # NOQA

from datetime import datetime  # NOQA

db = SQLAlchemy()

from sqlalchemy_utils import force_auto_coercion, force_instant_defaults  # NOQA

force_auto_coercion()
force_instant_defaults()

from flask_login import LoginManager  # NOQA

login_manager = LoginManager()
##########################################################################################
# IMPORTANT: Do not uncomment the line below, it will break the oauth login management
#            that is managed by @login_manager.request_loader
# login_manager.session_protection = "strong"
##########################################################################################

from flask_paranoid import Paranoid  # NOQA

from flask_marshmallow import Marshmallow  # NOQA

marshmallow = Marshmallow()

from .auth import OAuth2Provider  # NOQA

oauth2 = OAuth2Provider()

from .email import mail  # NOQA

from flask_minify import minify  # NOQA

from . import edm  # NOQA

from . import api  # NOQA

import stripe  # NOQA


##########################################################################################


class JsonEncodedDict(db.TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""

    impl = db.Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        else:
            return json.loads(value)


class GUID(db.TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return '%.32x' % uuid.UUID(value).int
            else:
                # hexstring
                return '%.32x' % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class TimestampViewed(Timestamp):
    """Adds `viewed` column to a derived declarative model."""

    viewed = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def view(self):
        self.updated = datetime.utcnow()


##########################################################################################


mutable.MutableDict.associate_with(JsonEncodedDict)

db.GUID = GUID


##########################################################################################


def init_app(app):
    """
    Application extensions initialization.
    """
    extensions = (
        logging,
        cross_origin_resource_sharing,
        db,
        login_manager,
        marshmallow,
        api,
        oauth2,
        mail,
        edm,
    )
    for extension in extensions:
        extension.init_app(app)

    minify(app=app)

    paranoid = Paranoid(app)
    paranoid.redirect_view = '/'

    # Initialize Stripe payment
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
