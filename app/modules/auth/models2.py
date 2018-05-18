import time, enum
from authlib.flask.oauth2.sqla import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)
from sqlalchemy_utils.types import ScalarListType

from app.extensions import db
from app.modules.users.models import User


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    class ClientTypes(str, enum.Enum):
        public = 'public'
        confidential = 'confidential'

    client_type = db.Column(db.Enum(ClientTypes), default=ClientTypes.public, nullable=False)
    default_scopes = db.Column(ScalarListType(separator=' '), nullable=False)

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

    def is_refresh_token_expired(self):
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at < time.time()
