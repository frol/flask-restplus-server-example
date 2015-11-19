# encoding: utf-8
"""
OAuth2 provider models.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""

from datetime import datetime, timedelta

from flask.ext.login import current_user
from flask.ext.sqlalchemy import SQLAlchemy

from app import db


class OAuth2Client(db.Model):
    __tablename__ = 'oauth2_client'

    client_id = db.Column(db.String(length=40), primary_key=True)
    client_secret = db.Column(db.String(length=55), nullable=False)

    user_id = db.Column(db.ForeignKey('user.id', ondelete='CASCADE'), index=True, nullable=False)
    user = db.relationship('User')

    _redirect_uris = db.Column(db.Text, default='', nullable=False)
    _default_scopes = db.Column(db.Text, default='', nullable=False)

    @property
    def client_type(self):
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        redirect_uris = self.redirect_uris
        if redirect_uris:
            return redirect_uris[0]
        return None

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []

    @classmethod
    def find(cls, client_id):
        return cls.query.get(client_id)


class OAuth2Grant(db.Model):
    __tablename__ = 'oauth2_grant'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.ForeignKey('user.id', ondelete='CASCADE'), index=True, nullable=False)
    user = db.relationship('User')

    client_id = db.Column(
        db.String(length=40),
        db.ForeignKey('oauth2_client.client_id'),
        index=True,
        nullable=False,
    )
    client = db.relationship('OAuth2Client')

    code = db.Column(db.String(length=255), index=True, nullable=False)

    redirect_uri = db.Column(db.String(length=255), nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    _scopes = db.Column(db.Text, nullable=False)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    @classmethod
    def find(cls, client_id, code):
        return cls.query.filter_by(client_id=client_id, code=code).first()

    @classmethod
    def create(cls, client_id, code, request, *args, **kwargs):
        # TODO: review expiration time
        # decide the expires time yourself
        expires = datetime.utcnow() + timedelta(seconds=100)
        grant = cls(
            client_id=client_id,
            code=code['code'],
            redirect_uri=request.redirect_uri,
            _scopes=' '.join(request.scopes),
            user=current_user,
            expires=expires
        )
        db.session.add(grant)
        db.session.commit()
        return grant


class OAuth2Token(db.Model):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(length=40),
        db.ForeignKey('oauth2_client.client_id'),
        index=True,
        nullable=False,
    )
    client = db.relationship('OAuth2Client')

    user_id = db.Column(db.ForeignKey('user.id', ondelete='CASCADE'), index=True, nullable=False)
    user = db.relationship('User')

    # currently only bearer is supported
    token_type = db.Column(db.String(length=40), nullable=False)

    access_token = db.Column(db.String(length=255), unique=True, nullable=False)
    refresh_token = db.Column(db.String(length=255), unique=True, nullable=True)
    expires = db.Column(db.DateTime, nullable=False)
    _scopes = db.Column(db.Text, nullable=False)

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    @classmethod
    def find(cls, access_token=None, refresh_token=None):
        if access_token:
            return cls.query.filter_by(access_token=access_token).first()
        elif refresh_token:
            return cls.query.filter_by(refresh_token=refresh_token).first()

    @classmethod
    def create(cls, token, request, *args, **kwargs):
        # make sure that every client has only one token connected to a user
        db.session.query(OAuth2Token).filter_by(
            client_id=request.client.client_id,
            user_id=request.user.id
        ).delete()
        
        expires_in = token.pop('expires_in')
        expires = datetime.utcnow() + timedelta(seconds=expires_in)

        tok = OAuth2Token(
            access_token=token['access_token'],
            refresh_token=token.get('refresh_token'),
            token_type=token['token_type'],
            _scopes=token['scope'],
            expires=expires,
            client_id=request.client.client_id,
            user_id=request.user.id,
        )
        db.session.add(tok)
        db.session.commit()
