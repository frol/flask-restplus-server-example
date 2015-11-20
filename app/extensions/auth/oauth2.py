# coding: utf-8
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""

from flask.ext.oauthlib import provider
from werkzeug import exceptions as http_exceptions

from app.extensions import api


class OAuth2RequestValidator(provider.OAuth2RequestValidator):

    def __init__(self):
        from app.modules.auth.models import OAuth2Client, OAuth2Grant, OAuth2Token
        super(OAuth2RequestValidator, self).__init__(
            usergetter=self._usergetter,
            clientgetter=OAuth2Client.find,
            tokengetter=OAuth2Token.find,
            grantgetter=OAuth2Grant.find,
            tokensetter=OAuth2Token.create,
            grantsetter=OAuth2Grant.create,
        )
    
    def _usergetter(self, username, password, client, request):
        # Avoid circular dependencies
        from app.modules.users.models import User
        return User.find_with_password(username, password)

    def client_authentication_required(self, request, *args, **kwargs):
        # XXX: patched version
        # TODO: implement it better in oauthlib, but for now we excluded
        # password flow from `client_secret` requirement.
        grant_types = ('authorization_code', 'refresh_token')
        return request.grant_type in grant_types


class OAuth2Provider(provider.OAuth2Provider):

    def __init__(self, *args, **kwargs):
        super(OAuth2Provider, self).__init__(*args, **kwargs)
        # XXX: it would be great if flask-oauthlib won't override existing
        # methods, so we can implement `_invalid_response` as a method instead
        # of lambda.
        self._invalid_response = lambda req: api.abort(code=http_exceptions.Unauthorized.code)

    def init_app(self, app):
        super(OAuth2Provider, self).init_app(app)
        self._validator = OAuth2RequestValidator()
