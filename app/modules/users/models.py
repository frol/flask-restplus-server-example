# encoding: utf-8
"""
User database models
--------------------
"""
import enum
import logging

from flask import url_for
from sqlalchemy_utils import types as column_types, Timestamp

from flask_login import current_user
from app.extensions import db
from app.extensions.api.parameters import _get_is_static_role_property
from app.modules.assets.models import Asset

import datetime
import pytz


log = logging.getLogger(__name__)


PST = pytz.timezone('US/Pacific')


def _format_datetime(dt):
    if dt is None:
        return None
    return dt.strftime('%I:%M %p').strip('0')


def _get_age_property():
    """
    A helper function that aims to provide a property getter and setter
    for static roles.

    Returns:
        property_method (property) - preconfigured getter and setter property
        for accessing role.
    """
    @property
    def _age_property(self):
        delta_years = None
        delta_months = None

        default_birth_day = 1

        try:
            if self.birth_month is not None and self.birth_year is not None:
                birth_date = datetime.date(self.birth_year, self.birth_month, default_birth_day)
            else:
                birth_date = None
        except:
            birth_date = None

        if birth_date is not None:
            now = datetime.datetime.now(tz=PST)
            today_date = datetime.date(now.year, now.month, default_birth_day)

            delta_years = today_date.year - birth_date.year
            delta_months = today_date.month - birth_date.month
            if delta_months < 0:
                delta_years -= 1
                delta_months %= 12

        age = {
            'years': delta_years,
            'months': delta_months,
        }

        return age

    @_age_property.setter
    def _age_property(self, value):
        log.error('Cannot set User.age property')
        pass

    _age_property.fget.__name__ = 'age'
    return _age_property


class User(db.Model, Timestamp):
    """
    User database model.
    """

    id               = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    username         = db.Column(db.String(length=120), unique=True, nullable=False)
    email            = db.Column(db.String(length=120), unique=True, nullable=False)

    password         = db.Column(
        column_types.PasswordType(
            max_length=128,
            schemes=('bcrypt', )
        ),
        nullable=False
    )

    # title_name    = db.Column(db.String(length=8),  default='', nullable=True)
    first_name       = db.Column(db.String(length=30), default='', nullable=False)
    middle_name      = db.Column(db.String(length=30), default='', nullable=True)
    last_name        = db.Column(db.String(length=30), default='', nullable=False)
    suffix_name      = db.Column(db.String(length=8),  default='', nullable=True)

    birth_month      = db.Column(db.Integer, default=None, nullable=True)
    birth_year       = db.Column(db.Integer, default=None, nullable=True)
    age              = _get_age_property()

    phone            = db.Column(db.String(length=20),  nullable=True)

    address_line1    = db.Column(db.String(length=120), nullable=True)
    address_line2    = db.Column(db.String(length=120), nullable=True)
    address_city     = db.Column(db.String(length=120), nullable=True)
    address_state    = db.Column(db.String(length=30),  nullable=True)
    address_zip      = db.Column(db.String(length=10),  nullable=True)

    profile_asset_id = db.Column(db.Integer(), nullable=True)

    class StaticRoles(enum.Enum):
        # pylint: disable=missing-docstring,unsubscriptable-object
        INTERNAL    = (0x8000, "Internal")
        ADMIN       = (0x4000, "Site Administrator")
        STAFF       = (0x2000, "Staff Member")
        ACTIVE      = (0x1000, "Active Account")

        SETUP       = (0x0800, "Account in Setup")
        RESET       = (0x0400, "Account in Password Reset")
        ALPHA       = (0x0200, "Enrolled in Alpha")
        BETA        = (0x0100, "Enrolled in Beta")

        @property
        def mask(self):
            return self.value[0]

        @property
        def title(self):
            return self.value[1]

    static_roles = db.Column(db.Integer, default=0, nullable=False)

    is_internal        = _get_is_static_role_property('is_internal',        StaticRoles.INTERNAL)
    is_admin           = _get_is_static_role_property('is_admin',           StaticRoles.ADMIN)
    is_staff           = _get_is_static_role_property('is_staff',           StaticRoles.STAFF)
    is_active          = _get_is_static_role_property('is_active',          StaticRoles.ACTIVE)

    in_beta            = _get_is_static_role_property('in_beta',            StaticRoles.BETA)
    in_alpha           = _get_is_static_role_property('in_alpha',           StaticRoles.ALPHA)

    in_reset           = _get_is_static_role_property('in_reset',           StaticRoles.RESET)
    in_setup           = _get_is_static_role_property('in_setup',           StaticRoles.SETUP)

    def __repr__(self):
        return (
            "<{class_name}("
            "id={self.id}, "
            "username=\"{self.username}\", "
            "email=\"{self.email}\", "
            "is_internal={self.is_internal}, "
            "is_admin={self.is_admin}, "
            "is_staff={self.is_staff}, "
            "is_active={self.is_active}, "
            ")>".format(
                class_name=self.__class__.__name__,
                self=self
            )
        )

    def has_static_role(self, role):
        return (self.static_roles & role.mask) != 0

    def set_static_role(self, role):
        if self.has_static_role(role):
            return
        self.static_roles |= role.mask

    def unset_static_role(self, role):
        if not self.has_static_role(role):
            return
        self.static_roles ^= role.mask

    def check_owner(self, user):
        return self == user

    def check_supervisor(self, user):
        return self.check_owner(user)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_email_confirmed(self):
        from app.modules.auth.models import Code, CodeTypes
        # Get any codes that fit this request
        code = Code.query.filter_by(user=self, code_type=CodeTypes.email).order_by(Code.created.desc()).first()
        if code is None:
            return False
        return code.is_resolved

    def get_id(self):
        return self.username

    def get_codes(self, code_type, **kwargs):
        # This import for Code needs to be local
        from app.modules.auth.models import Code
        code = Code.get(self, code_type, **kwargs)
        return code

    def get_invite_code(self):
        # This import for Code needs to be local
        from app.modules.auth.models import CodeTypes
        return self.get_codes(CodeTypes.invite, replace=True)

    def get_email_confirmation_code(self):
        # This import for Code needs to be local
        from app.modules.auth.models import CodeTypes
        return self.get_codes(CodeTypes.email, replace=True)

    def get_account_recovery_code(self):
        # This import for Code needs to be local
        from app.modules.auth.models import CodeTypes
        return self.get_codes(CodeTypes.recover, replace=True, replace_ttl=None)

    def lockout(self):
        from app.modules.auth.models import OAuth2Client, OAuth2Grant, OAuth2Token, Code

        # Disable permissions
        self.is_staff  = False
        self.is_admin  = False
        self.is_active = False
        self.in_reset  = False
        self.in_setup  = False

        with db.session.begin():
            db.session.merge(self)
        db.session.refresh(self)

        # Logout of sessions and API keys
        auth_list = []
        auth_list += OAuth2Token.query.filter_by(user_id=self.id).all()
        auth_list += OAuth2Grant.query.filter_by(user_id=self.id).all()
        auth_list += OAuth2Client.query.filter_by(user_id=self.id).all()
        auth_list += Code.query.filter_by(user_id=self.id).all()
        for auth_ in auth_list:
            auth_.delete()

        return self

    @classmethod
    def find(cls, username=None, email=None, password=None):
        assert username is None or email is None, 'Must specify only ONE (username or email) for User lookup'

        # Look-up via username or email
        if username is not None:
            user = User.query.filter_by(username=username).first()
        elif email is not None:
            user = User.query.filter_by(email=email).first()
        else:
            user = None

        # If a password is specified, do a check
        if user is not None and password is not None:
            if user.password != password:
                user = None

        # Check for invalid
        if not user:
            user = None

        # Return User or None
        return user

    @classmethod
    def suggest_password(cls):
        from xkcdpass import xkcd_password as xp
        xp_wordfile = xp.locate_wordfile()
        xp_wordlist = xp.generate_wordlist(wordfile=xp_wordfile, min_length=4, max_length=6, valid_chars='[a-z]')
        suggested_password = xp.generate_xkcdpassword(xp_wordlist, numwords=4, acrostic='wild', delimiter=' ')
        return suggested_password

    @ property
    def picture(self):
        asset = Asset.query.filter_by(id=self.profile_asset_id).first()
        if asset is None:
            placeholder_id = (self.id % 7) + 1
            filename = 'images/placeholder_profile_%d.png' % (placeholder_id, )
            return url_for('static', filename=filename)
        return url_for('frontend.asset', code=asset.code)
