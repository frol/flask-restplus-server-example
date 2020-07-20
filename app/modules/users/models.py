# -*- coding: utf-8 -*-
"""
User database models
--------------------
"""
import enum
import logging

from flask import url_for, current_app
import sqlalchemy
from sqlalchemy_utils import types as column_types

from flask_login import current_user  # NOQA
from app.extensions import db, TimestampViewed
from app.extensions.edm import EDMObjectMixin
from app.extensions.api.parameters import _get_is_static_role_property

from app.modules.assets.models import Asset

import pytz
import uuid

import tqdm

log = logging.getLogger(__name__)


PST = pytz.timezone('US/Pacific')


class UserEDMMixin(EDMObjectMixin):

    # fmt: off
    # The EDM attribute for the version, if reported
    EDM_VERSION_ATTRIBUTE = 'version'

    #
    EDM_LOG_ATTRIBUTES = [
        'emailAddress',
    ]

    EDM_ATTRIBUTE_MAPPING = {
        # Ignorerd
        'id'                    : None,
        'lastLogin'             : None,
        'username'              : None,

        # Attributes
        'acceptedUserAgreement' : 'accepted_user_agreement',
        'affiliation'           : 'affiliation',
        'emailAddress'          : 'email',
        'fullName'              : 'full_name',
        'receiveEmails'         : 'receive_notification_emails',
        'sharing'               : 'shares_data',
        'userURL'               : 'website',
        'version'               : 'version',

        # Functions
        'organizations'         : '_process_edm_user_organization',
        'profileImageUrl'       : '_process_edm_user_profile_url',
    }
    # fmt: on

    @classmethod
    def edm_sync_users(cls, verbose=True, refresh=False):
        from app.modules.auth.models import _generate_salt

        edm_users = current_app.edm.get_users()

        if verbose:
            log.info('Checking %d EDM users against local cache...' % (len(edm_users),))

        new_users = []
        stale_users = []
        with db.session.begin():
            for guid in tqdm.tqdm(edm_users):
                user = edm_users[guid]
                version = user.get('version', None)
                assert version is not None

                user = User.query.filter(User.guid == guid).first()

                if user is None:
                    email = '%s@localhost' % (guid,)
                    password = _generate_salt(128)
                    user = User(
                        guid=guid,
                        email=email,
                        password=password,
                        version=None,
                        is_active=True,
                    )
                    db.session.add(user)
                    new_users.append(user)

                if user.version != version or refresh:
                    stale_users.append((user, version))

        if verbose:
            log.info('Added %d new users' % (len(new_users),))

        if verbose:
            log.info('Updating %d stale users using EDM...' % (len(stale_users),))

        updated_users = []
        failed_users = []
        for user, version in tqdm.tqdm(stale_users):
            try:
                user.edm_sync(version)
                updated_users.append(user)
            except sqlalchemy.exc.IntegrityError:
                log.error('Error updating user %r' % (user,))
                failed_users.append(user)

        return edm_users, new_users, updated_users, failed_users

    def edm_sync(self, version):
        response = current_app.edm.get_user_data(self.guid)

        assert response.success
        data = response.result

        assert uuid.UUID(data.id) == self.guid

        self._process_edm_data(data, version)

    def _process_edm_user_profile_url(self, url):
        log.warning('User._process_edm_profile_url() not implemented yet')

    def _process_edm_user_organization(self, org):
        log.warning('User._process_edm_user_organization() not implemented yet')


class User(db.Model, TimestampViewed, UserEDMMixin):
    """
    User database model.
    """

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name
    version = db.Column(db.Integer, default=None, nullable=True)

    email = db.Column(db.String(length=120), index=True, unique=True, nullable=False)

    password = db.Column(
        column_types.PasswordType(max_length=128, schemes=('bcrypt',)), nullable=False
    )  # can me migrated from EDM field "password"

    full_name = db.Column(
        db.String(length=120), default='', nullable=False
    )  # can be migrated from EDM field "fullName"
    website = db.Column(
        db.String(length=120), nullable=True
    )  # can be migrated from EDM field "userURL"
    location = db.Column(db.String(length=120), nullable=True)
    affiliation = db.Column(
        db.String(length=120), nullable=True
    )  # can be migrated from BE field "affiliation"
    forum_id = db.Column(db.String(length=120), nullable=True)
    locale = db.Column(db.String(length=20), default='EN', nullable=True)

    accepted_user_agreement = db.Column(
        db.Boolean, default=False, nullable=False
    )  # can be migrated from EDM field "acceptedUserAgreement"
    use_usa_date_format = db.Column(db.Boolean, default=True, nullable=False)
    show_email_in_profile = db.Column(db.Boolean, default=False, nullable=False)
    receive_notification_emails = db.Column(
        db.Boolean, default=True, nullable=False
    )  # can be migrated from BE field "receiveEmails"
    receive_newsletter_emails = db.Column(db.Boolean, default=False, nullable=False)
    shares_data = db.Column(
        db.Boolean, default=True, nullable=False
    )  # can be migrated from BE field "sharing"

    default_identification_catalogue = db.Column(
        db.GUID, nullable=True
    )  # this may just be a string, however EDM wants to do ID catalogues

    profile_asset_guid = db.Column(
        db.GUID, nullable=True
    )  # should be reconciled with Jon's MediaAsset class
    footer_logo_asset_guid = db.Column(
        db.GUID, nullable=True
    )  # should be reconciled with Jon's MediaAsset class

    class StaticRoles(enum.Enum):
        # pylint: disable=missing-docstring,unsubscriptable-object
        INTERNAL = (0x8000, 'Internal')
        ADMIN = (0x4000, 'Site Administrator')
        STAFF = (0x2000, 'Staff Member')
        ACTIVE = (0x1000, 'Active Account')

        SETUP = (0x0800, 'Account in Setup')
        RESET = (0x0400, 'Account in Password Reset')
        ALPHA = (0x0200, 'Enrolled in Alpha')
        BETA = (0x0100, 'Enrolled in Beta')

        @property
        def mask(self):
            return self.value[0]

        @property
        def title(self):
            return self.value[1]

    static_roles = db.Column(db.Integer, default=0, nullable=False)

    is_internal = _get_is_static_role_property('is_internal', StaticRoles.INTERNAL)
    is_admin = _get_is_static_role_property('is_admin', StaticRoles.ADMIN)
    is_staff = _get_is_static_role_property('is_staff', StaticRoles.STAFF)
    is_active = _get_is_static_role_property('is_active', StaticRoles.ACTIVE)

    in_beta = _get_is_static_role_property('in_beta', StaticRoles.BETA)
    in_alpha = _get_is_static_role_property('in_alpha', StaticRoles.ALPHA)

    in_reset = _get_is_static_role_property('in_reset', StaticRoles.RESET)
    in_setup = _get_is_static_role_property('in_setup', StaticRoles.SETUP)

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
            'email="{self.email}", '
            'is_internal={self.is_internal}, '
            'is_admin={self.is_admin}, '
            'is_staff={self.is_staff}, '
            'is_active={self.is_active}, '
            ')>'.format(class_name=self.__class__.__name__, self=self)
        )

    @classmethod
    def suggest_password(cls):
        from xkcdpass import xkcd_password as xp

        xp_wordfile = xp.locate_wordfile()
        xp_wordlist = xp.generate_wordlist(
            wordfile=xp_wordfile, min_length=4, max_length=6, valid_chars='[a-z]'
        )
        suggested_password = xp.generate_xkcdpassword(
            xp_wordlist, numwords=4, acrostic='wild', delimiter=' '
        )
        return suggested_password

    @classmethod
    def find(cls, email=None, password=None, edm_login_fallback=True):
        # Look-up via email

        if email is None:
            return None

        email_candidates = [
            email,
            '%s@localhost' % (email,),
        ]
        for email_candidate in email_candidates:

            user = cls.query.filter(User.email == email_candidate).first()

            if password is None:
                # If no password was provided to check, return any user account we find
                if user is not None:
                    return user
            else:
                # Check local Houston password first
                if user is not None:
                    # We found the user, check their provided password
                    if user.password == password:
                        return user

                # As a fallback, check all EDMs if the user can login
                if edm_login_fallback:
                    # We want to check the EDM even if we don't have a local user record
                    if current_app.edm.check_user_login(email_candidate, password):
                        log.info('User authenticated via EDM: %r' % (email_candidate,))

                        if user is not None:
                            # We authenticated a local user against an EDM (but the local password failed)
                            if user.password != password:
                                # The user passed the login with an EDM, update local password
                                log.warning(
                                    "Updating user's local password: %r" % (user,)
                                )
                                user = user.set_password(password)
                            return user
                        else:
                            log.danger(
                                'The user authenticated via EDM but has no local user record'
                            )
                            # Try syncing all users from EDM
                            cls.edm_sync_users()
                            # If the user was just synced, go grab it (recursively) and return
                            user = cls.find(email=email, edm_login_fallback=False)
                            return user

        # If we have gotten here, one of these things happened:
        #    1) the user wasn't found
        #    2) the user's password was provided and was incorrect
        #    3) the user authenticated against the EDM but has no local user record

        return None

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
        code = (
            Code.query.filter_by(user=self, code_type=CodeTypes.email)
            .order_by(Code.created.desc())
            .first()
        )
        if code is None:
            return False
        return code.is_resolved

    @property
    def picture(self):
        asset = Asset.query.filter_by(id=self.profile_asset_guid).first()
        if asset is None:
            placeholder_guid = (self.guid % 7) + 1
            filename = 'images/placeholder_profile_%d.png' % (placeholder_guid,)
            return url_for('static', filename=filename)
        return url_for('frontend.asset', code=asset.code)

    def get_id(self):
        return self.guid

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

    def set_password(self, password=None):
        if password is None:
            # Generate a random password for the user
            from app.modules.auth.models import _generate_salt

            password = _generate_salt(128)

        self.password = password
        with db.session.begin():
            db.session.merge(self)
        db.session.refresh(self)

        return self

    def lockout(self):
        from app.modules.auth.models import OAuth2Client, OAuth2Grant, OAuth2Token, Code

        # Disable permissions
        self.is_staff = False
        self.is_admin = False
        self.is_active = False
        self.in_reset = False
        self.in_setup = False

        with db.session.begin():
            db.session.merge(self)
        db.session.refresh(self)

        # Logout of sessions and API keys
        auth_list = []
        auth_list += OAuth2Token.query.filter_by(user_guid=self.guid).all()
        auth_list += OAuth2Grant.query.filter_by(user_guid=self.guid).all()
        auth_list += OAuth2Client.query.filter_by(user_guid=self.guid).all()
        auth_list += Code.query.filter_by(user_guid=self.guid).all()
        for auth_ in auth_list:
            auth_.delete()

        return self
