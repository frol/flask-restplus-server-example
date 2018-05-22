import functools, logging
from authlib.flask.oauth2 import AuthorizationServer, ResourceProtector, current_token
from authlib.flask.oauth2.sqla import (
    create_query_client_func,
    create_save_token_func,
    create_revocation_endpoint,
    create_bearer_token_validator,
)
from authlib.specs.rfc6749 import grants
from werkzeug.security import gen_salt
from app.extensions import api, login_manager
from app.modules.users.models import User
from app.modules.auth.models import OAuth2Client, OAuth2AuthorizationCode, OAuth2Token
from flask_restplus_patched._http import HTTPStatus
from authlib.specs.rfc6750 import BearerTokenValidator as _BearerTokenValidator

log = logging.getLogger(__name__)


@login_manager.request_loader
def load_user_from_request(request):
    """
    Load user from OAuth2 Authentication header.
    """
    from app.modules.users.models import User
    if current_token:
        user = current_token.user
        if user:
            return user
        user_id = current_token.user.id
        if user_id:
            return User.query.get(user_id)
    return None

def api_invalid_response(req):
    """
    This is a default handler for OAuth2Provider, which raises abort exception
    with error message in JSON format.
    """
    # pylint: disable=unused-argument
    api.abort(code=HTTPStatus.UNAUTHORIZED.value)


class BearerTokenValidator(_BearerTokenValidator):
    def authenticate_token(self, token_string):
        return OAuth2Token.query.filter_by(access_token=token_string).first()

    def request_invalid(self, request):
        return False

    def token_revoked(self, token):
        # TODO: return token.revoked
        return token.revoked

class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    def create_authorization_code(self, client, grant_user, request):
        from app.extensions import db
        code = gen_salt(48)
        item = OAuth2AuthorizationCode(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=grant_user.id,
        )
        db.session.add(item)
        db.session.commit()
        return code

    def parse_authorization_code(self, code, client):
        item = OAuth2AuthorizationCode.query.filter_by(
            code=code, client_id=client.client_id).first()
        if item and not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code):
        from app.extensions import db
        db.session.delete(authorization_code)
        db.session.commit()

    def authenticate_user(self, authorization_code):
        return User.query.get(authorization_code.user_id)


class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    def authenticate_user(self, username, password):
        return User.find_with_password(username, password)


class RefreshTokenGrant(grants.RefreshTokenGrant):
    def authenticate_refresh_token(self, refresh_token):
        item = OAuth2Token.query.filter_by(refresh_token=refresh_token).first()
        if item and not item.is_refresh_token_expired():
            return item

    def authenticate_user(self, credential):
        return User.query.get(credential.user_id)


class OAuth2ResourceProtector(ResourceProtector):
    def __init__( self ):
        super().__init__()


class OAuth2Provider(AuthorizationServer):
    def __init__(self):
        super().__init__()
        self._require_oauth = None

    def init_app( self, app, query_client=None, save_token=None ):
        from app.extensions import db
        if query_client is None:
            query_client = create_query_client_func(db.session, OAuth2Client)
        if save_token is None:
            save_token = create_save_token_func(db.session, OAuth2Token)

        super().init_app(
            app, query_client=query_client, save_token=save_token)

        # support all grants
        self.register_grant(grants.ImplicitGrant)
        self.register_grant(grants.ClientCredentialsGrant)
        self.register_grant(AuthorizationCodeGrant)
        self.register_grant(PasswordGrant)
        self.register_grant(RefreshTokenGrant)

        # support revocation
        revocation_cls = create_revocation_endpoint(db.session, OAuth2Token)
        self.register_endpoint(revocation_cls)

        # protect resource
        bearer_cls = create_bearer_token_validator(db.session, OAuth2Token)
        OAuth2ResourceProtector.register_token_validator(bearer_cls())
        self._require_oauth = OAuth2ResourceProtector()

    def require_oauth(self, *args, **kwargs):
        # pylint: disable=arguments-differ
        """
        A decorator to protect a resource with specified scopes. Access Token
        can be fetched from the specified locations (``headers`` or ``form``).

        Arguments:
            locations (list): a list of locations (``headers``, ``form``) where
                the access token should be looked up.

        Returns:
            function: a decorator.
        """
        locations = kwargs.get('locations', ('cookies',))   # don't want to pop - original decorator may need
        origin_decorator = self._require_oauth(*args, **kwargs)

        def decorator(func):
            # pylint: disable=missing-docstring
            from flask import request

            origin_decorated_func = origin_decorator(func)

            @functools.wraps(origin_decorated_func)
            def wrapper(*args, **kwargs):
                # pylint: disable=missing-docstring
                if 'headers' not in locations:
                    # Invalidate authorization if developer specifically
                    # disables the lookup in the headers. (this may or may not be worth all the hassle)
                    request.authorization = '!'
                # don't think we need below lines because bearer validator already registered
                # if 'form' in locations:
                #     if 'access_token' in request.form:
                #         request.authorization = 'Bearer %s' % request.form['access_token']

                return origin_decorated_func(*args, **kwargs)

            return wrapper

        return decorator
