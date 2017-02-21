# encoding: utf-8
# pylint: disable=no-self-use
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""

from datetime import datetime, timedelta
import logging

from flask_login import current_user
from flask_oauthlib import provider
from flask_restplus_patched._http import HTTPStatus
import sqlalchemy

from app.extensions import api, db


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class OAuth2RequestValidator(provider.OAuth2RequestValidator):
    """
    A project-specific implementation of OAuth2RequestValidator, which connects
    our User and OAuth2* implementations together.
    """

    def __init__(self):
        from app.modules.auth.models import OAuth2Client, OAuth2Grant, OAuth2Token
        self._client_class = OAuth2Client
        self._grant_class = OAuth2Grant
        self._token_class = OAuth2Token
        super(OAuth2RequestValidator, self).__init__(
            usergetter=self._usergetter,
            clientgetter=self._client_class.find,
            tokengetter=self._token_class.find,
            grantgetter=self._grant_class.find,
            tokensetter=self._tokensetter,
            grantsetter=self._grantsetter,
        )

    def _usergetter(self, username, password, client, request):
        # pylint: disable=method-hidden,unused-argument
        # Avoid circular dependencies
        from app.modules.users.models import User
        return User.find_with_password(username, password)

    def _tokensetter(self, token, request, *args, **kwargs):
        # pylint: disable=method-hidden,unused-argument
        # TODO: review expiration time
        expires_in = token.pop('expires_in')
        expires = datetime.utcnow() + timedelta(seconds=expires_in)

        token_instance = self._token_class(
            access_token=token['access_token'],
            refresh_token=token.get('refresh_token'),
            token_type=token['token_type'],
            scopes=[scope for scope in token['scope'].split(' ') if scope],
            expires=expires,
            client_id=request.client.client_id,
            user_id=request.user.id,
        )
        db.session.add(token_instance)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            log.exception("Token-setter has failed.")
            return None
        return token_instance

    def _grantsetter(self, client_id, code, request, *args, **kwargs):
        # pylint: disable=method-hidden,unused-argument
        # TODO: review expiration time
        # decide the expires time yourself
        expires = datetime.utcnow() + timedelta(seconds=100)
        grant_instance = self._grant_class(
            client_id=client_id,
            code=code['code'],
            redirect_uri=request.redirect_uri,
            scopes=request.scopes,
            user=current_user,
            expires=expires
        )
        db.session.add(grant_instance)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            log.exception("Grant-setter has failed.")
            return None
        return grant_instance


def api_invalid_response(req):
    """
    This is a default handler for OAuth2Provider, which raises abort exception
    with error message in JSON format.
    """
    # pylint: disable=unused-argument
    api.abort(code=HTTPStatus.UNAUTHORIZED.value)


class OAuth2Provider(provider.OAuth2Provider):
    """
    A helper class which connects OAuth2RequestValidator with OAuth2Provider.
    """

    def __init__(self, *args, **kwargs):
        super(OAuth2Provider, self).__init__(*args, **kwargs)
        self.invalid_response(api_invalid_response)

    def init_app(self, app):
        super(OAuth2Provider, self).init_app(app)
        self._validator = OAuth2RequestValidator()
