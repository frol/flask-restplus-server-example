# -*- coding: utf-8 -*-
"""
OAuth2 provider models.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""
import logging
import enum

from sqlalchemy import or_
from sqlalchemy_utils import Timestamp
from sqlalchemy_utils.types import ScalarListType

from app.extensions import db
from app.modules.users.models import User

import datetime
import pytz

import random
import uuid


log = logging.getLogger(__name__)


PST = pytz.timezone('US/Pacific')


CODE_VALID_CHARACTERS = [
    '0',
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',
    'A',
    'B',
    'C',
    'D',
    'E',
    'F',
]


class CodeTypes(str, enum.Enum):
    invite = 'invite'
    email = 'email'
    recover = 'recover'
    onetime = 'onetime'


class CodeDecisions(str, enum.Enum):
    unknown = 'unknown'
    error = 'error'
    expired = 'expired'
    dismiss = 'dismiss'
    reject = 'reject'

    # Accept and override should be treated the same functionally in the code
    accept = 'accept'
    override = 'override'


TTL_MINUTE_DEFAULT = 17

CODE_SETTINGS = {
    None: {
        'ttl': 7,  # The default code should last 7 days, rounded up to (local midnight time - 1 second) of the day it will expire
        'len': 8,  # The default code should be 8 (hexidecimal) characters long
    },
    CodeTypes.invite: {'ttl': 14, 'len': 8,},
    CodeTypes.email: {'ttl': 7, 'len': 64,},
    CodeTypes.recover: {'ttl': 3, 'len': 64,},
    CodeTypes.onetime: {'ttl': None, 'len': 8,},  # None will default to 10 minutes
}


class OAuth2Client(db.Model):
    """
    Model that binds OAuth2 Client ID and Secret to a specific User.
    """

    __tablename__ = 'oauth2_client'

    guid = db.Column(db.GUID, default=uuid.uuid4, primary_key=True)
    secret = db.Column(db.String(length=64), nullable=False)

    user_guid = db.Column(
        db.ForeignKey('user.guid', ondelete='CASCADE'), index=True, nullable=False
    )
    user = db.relationship(User)

    class ClientLevels(str, enum.Enum):
        public = 'public'
        session = 'session'
        confidential = 'confidential'

    level = db.Column(db.Enum(ClientLevels), default=ClientLevels.public, nullable=False)
    redirect_uris = db.Column(ScalarListType(separator=' '), default=[], nullable=False)
    default_scopes = db.Column(ScalarListType(separator=' '), nullable=False)

    @property
    def default_redirect_uri(self):
        redirect_uris = self.redirect_uris
        if redirect_uris:
            return redirect_uris[0]
        return None

    @classmethod
    def find(cls, client_guid):
        if not client_guid:
            return None
        return cls.query.get(client_guid)

    def validate_scopes(self, scopes):
        # The only reason for this override is that Swagger UI has a bug which leads to that
        # `scope` parameter contains extra spaces between scopes:
        # https://github.com/frol/flask-restplus-server-example/issues/131
        return set(self.default_scopes).issuperset(set(scopes) - {''})

    def delete(self):
        with db.session.begin():
            db.session.delete(self)


class OAuth2Grant(db.Model):
    """
    Intermediate temporary helper for OAuth2 Grants.
    """

    __tablename__ = 'oauth2_grant'

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name

    user_guid = db.Column(
        db.ForeignKey('user.guid', ondelete='CASCADE'), index=True, nullable=False
    )
    user = db.relationship('User')

    client_guid = db.Column(
        db.GUID, db.ForeignKey('oauth2_client.guid'), index=True, nullable=False,
    )
    client = db.relationship('OAuth2Client')

    code = db.Column(db.String(length=255), index=True, nullable=False)

    redirect_uri = db.Column(db.String(length=255), nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    scopes = db.Column(ScalarListType(separator=' '), nullable=False)

    def delete(self):
        with db.session.begin():
            db.session.delete(self)

    @classmethod
    def find(cls, client_guid, code):
        return cls.query.filter_by(client_guid=client_guid, code=code).first()

    @property
    def is_expired(self):
        now_utc = datetime.datetime.now(tz=pytz.utc)
        expired = now_utc > self.expires.replace(tzinfo=pytz.utc)
        return expired


class OAuth2Token(db.Model):
    """
    OAuth2 Access Tokens storage model.
    """

    __tablename__ = 'oauth2_token'

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name

    client_guid = db.Column(
        db.GUID, db.ForeignKey('oauth2_client.guid'), index=True, nullable=False,
    )
    client = db.relationship('OAuth2Client')

    user_guid = db.Column(
        db.ForeignKey('user.guid', ondelete='CASCADE'), index=True, nullable=False
    )
    user = db.relationship('User')

    class TokenTypes(str, enum.Enum):
        # currently only bearer is supported
        Bearer = 'Bearer'

    token_type = db.Column(db.Enum(TokenTypes), nullable=False)

    access_token = db.Column(db.String(length=128), unique=True, nullable=False)
    refresh_token = db.Column(db.String(length=128), unique=True, nullable=True)
    expires = db.Column(db.DateTime, nullable=False)
    scopes = db.Column(ScalarListType(separator=' '), nullable=False)

    @classmethod
    def find(cls, access_token=None, refresh_token=None):
        if access_token:
            return cls.query.filter_by(access_token=access_token).first()
        if refresh_token:
            return cls.query.filter_by(refresh_token=refresh_token).first()
        return None

    def delete(self):
        with db.session.begin():
            db.session.delete(self)

    @property
    def is_expired(self):
        now_utc = datetime.datetime.now(tz=pytz.utc)
        expired = now_utc > self.expires.replace(tzinfo=pytz.utc)
        return expired


class Code(db.Model, Timestamp):
    """
    OAuth2 Access Tokens storage model.
    """

    __tablename__ = 'code'

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name

    user_guid = db.Column(db.GUID, db.ForeignKey('user.guid'), index=True, nullable=False)
    user = db.relationship(
        'User', backref=db.backref('codes', cascade='delete, delete-orphan')
    )

    code_type = db.Column(db.Enum(CodeTypes), index=True, nullable=False)

    accept_code = db.Column(db.String(length=64), index=True, unique=True, nullable=False)
    reject_code = db.Column(db.String(length=64), index=True, unique=True, nullable=False)

    expires = db.Column(db.DateTime, nullable=False)
    response = db.Column(db.DateTime, nullable=True)

    decision = db.Column(db.Enum(CodeDecisions), nullable=True)

    # __table_args__ = (
    #     db.UniqueConstraint(user_guid, code_type),
    # )

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
            'created={self.created}, '
            'type={self.code_type}, '
            'accept={self.accept_code}, '
            'reject={self.reject_code}, '
            'expires={self.expires}, '
            'is_expired={self.is_expired}, '
            'is_resolved={self.is_resolved}, '
            ')>'.format(class_name=self.__class__.__name__, self=self)
        )

    @classmethod
    def generate(cls, length=8):
        new_code = []
        while len(new_code) < length:
            candidate = random.choice(CODE_VALID_CHARACTERS)
            new_code.append(candidate)
        new_code = ''.join(new_code)
        return new_code

    @classmethod
    def get(
        cls,
        user,
        code_type,
        create=True,
        replace=False,
        replace_ttl=12 * 60,
        create_force=False,
    ):
        """ Replace will automatically invalidate any codes previously issued (above the replace_ttl value, in minutes)"""
        code_settings = CODE_SETTINGS.get(code_type, None)
        assert code_settings is not None, 'Code type was unrecognized: %r' % (code_type,)

        # Get any codes that fit this request
        existing_codes = (
            cls.query.filter_by(user=user, code_type=code_type)
            .order_by(cls.created.desc())
            .all()
        )
        valid_codes = [
            code
            for code in existing_codes
            if not code.is_expired and not code.is_resolved
        ]

        if replace:
            # Create a new code and delete any previous codes in the process
            if len(valid_codes) > 0:
                if replace_ttl is None:
                    delete_codes = valid_codes
                else:
                    replace_ttl_date = datetime.datetime.now(
                        tz=pytz.utc
                    ) - datetime.timedelta(minutes=replace_ttl)

                    delete_codes = [
                        valid_code
                        for valid_code in valid_codes
                        if valid_code.created.replace(tzinfo=pytz.utc) < replace_ttl_date
                    ]
                log.warning('Replacing codes, deleting %d' % (len(delete_codes),))
                with db.session.begin():
                    for delete_code in delete_codes:
                        db.session.delete(delete_code)

                # We have deleted all of the matching codes (respecting replace_ttl_minutes), re-run this function
                # It is possible to have sent an email confirmation code in the past hour and get it back
                return cls.get(user, code_type, replace=False, replace_ttl=replace_ttl)

        code = None
        if len(valid_codes) > 0:
            # Take the most recently generated valid code
            code = valid_codes[0]

        if code is None and create or create_force:
            # Create a new code
            now = datetime.datetime.now(tz=PST)

            while True:
                accept_code = cls.generate(code_settings.get('len'))
                reject_code = cls.generate(code_settings.get('len'))
                existing_accept_codes = cls.find(accept_code)
                existing_reject_codes = cls.find(reject_code)
                if len(existing_accept_codes) == 0 and len(existing_reject_codes) == 0:
                    # Found unique codes
                    break
                log.warning('Finding alternate codes, there was a conflict:')
                log.warning('\tCandidate   Accept Code  : %r' % (accept_code,))
                log.warning('\tConflicting Accept Codes : %r' % (existing_accept_codes,))
                log.warning('\tCandidate   Reject Code  : %r' % (reject_code,))
                log.warning('\tConflicting Reject Codes : %r' % (existing_reject_codes,))

            ttl_days = code_settings.get('ttl')
            if ttl_days is None or ttl_days < 0:
                ttl_minutes = TTL_MINUTE_DEFAULT if ttl_days is None else 0
                expires_ = now + datetime.timedelta(minutes=ttl_minutes)
                expires = datetime.datetime(
                    expires_.year,
                    expires_.month,
                    expires_.day,
                    expires_.hour,
                    expires_.minute,
                    expires_.second,
                    tzinfo=PST,
                )
            else:
                # Round up to (midnight - 1 second) of the TTL day
                expires_ = now + datetime.timedelta(days=ttl_days)
                expires = datetime.datetime(
                    expires_.year, expires_.month, expires_.day, 23, 59, 59, tzinfo=PST
                )

            expires_utc = expires.astimezone(pytz.utc)
            code_kwargs = {
                'user_guid': user.guid,
                'code_type': code_type,
                'accept_code': accept_code,
                'reject_code': reject_code,
                'expires': expires_utc,
            }
            with db.session.begin():
                code = Code(**code_kwargs)
                db.session.add(code)
            db.session.refresh(code)
            db.session.refresh(user)

        return code

    @classmethod
    def find(cls, code):
        matched_codes = (
            Code.query.filter(or_(Code.accept_code == code, Code.reject_code == code,))
            .order_by(cls.created.desc())
            .all()
        )
        return matched_codes

    @classmethod
    def cleanup(cls):
        codes = cls.query.all()
        old_codes = [code for code in codes if code.is_expired and not code.is_resolved]
        log.warning('Cleaning codes, deleting %d' % (len(old_codes),))
        with db.session.begin():
            for old_code in old_codes:
                db.session.delete(old_code)

        return None

    @classmethod
    def received(cls, code_str):
        # Strip code, keeping only valid characters

        if code_str is None:
            return CodeDecisions.error, None

        code_str = code_str.upper()
        code_str = ''.join([char for char in code_str if char in CODE_VALID_CHARACTERS])

        code_list = Code.find(code_str)
        if len(code_list) == 0:
            decision = CodeDecisions.unknown
            code = None
        elif len(code_list) > 1:
            decision = CodeDecisions.error
            code = code_list
        else:
            code = code_list[0]

            if code.is_expired:
                decision = CodeDecisions.expired
            elif code.is_resolved:
                decision = CodeDecisions.dismiss
            elif code_str in [code.accept_code]:
                decision = CodeDecisions.accept
                code.record(decision)
            elif code_str in [code.reject_code]:
                decision = CodeDecisions.reject
                code.record(decision)
            else:
                decision = CodeDecisions.error

        return decision, code

    @property
    def is_expired(self):
        now_utc = datetime.datetime.now(tz=pytz.utc)
        expired = now_utc > self.expires.replace(tzinfo=pytz.utc)
        return expired

    @property
    def is_resolved(self):
        resolved = self.response is not None
        return resolved

    def record(self, decision):
        self.decision = decision
        self.response = datetime.datetime.now(tz=pytz.utc)
        with db.session.begin():
            db.session.merge(self)
        db.session.refresh(self)
        return self

    def delete(self):
        with db.session.begin():
            db.session.delete(self)
