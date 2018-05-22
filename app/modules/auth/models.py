import time, enum
from authlib.flask.oauth2.sqla import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)
from sqlalchemy_utils.types import ScalarListType

from app.extensions import db


class MyOAuth2ClientMixin(OAuth2ClientMixin):
    def check_requested_scopes(self, scopes):
        if type(self.scope) == str:
            allowed = set(self.scope.split())
        elif type(self.scope) == list:
            allowed = set(self.scope)

        return allowed.issuperset(set(scopes))

class OAuth2Client(db.Model, MyOAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    class ClientTypes(str, enum.Enum):
        public = 'public'
        confidential = 'confidential'

    client_type = db.Column(db.Enum(ClientTypes), default=ClientTypes.public, nullable=False)
    default_scopes = db.Column(ScalarListType(separator=' '), nullable=False)
    scope = db.Column(ScalarListType(separator=' '), nullable=False)

    user = db.relationship('User')

    @property
    def default_redirect_uri(self):
        return self.get_default_redirect_uri()

    @classmethod
    def find(cls, client_id):
        if not client_id:
            return
        return cls.query.get(client_id)


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')
    revoked = db.Column(db.Boolean(name='revoked'), default=False)      # override because of bug in alembic

    def is_refresh_token_expired(self):
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at < time.time()
