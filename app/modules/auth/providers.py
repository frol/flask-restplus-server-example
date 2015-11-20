# coding: utf-8
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""

from flask.ext.oauthlib.provider import OAuth2Provider, OAuth2RequestValidator
from werkzeug.exceptions import Unauthorized

from app.extensions import api
from .models import OAuth2Client, OAuth2Grant, OAuth2Token


class CustomOAuth2RequestValidator(OAuth2RequestValidator):

    _clientgetter=OAuth2Client.find
    _tokengetter=OAuth2Token.find
    _grantgetter=OAuth2Grant.find
    _tokensetter=OAuth2Token.create
    _grantsetter=OAuth2Grant.create

    def __init__(self):
        pass
    
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


class CustomOAuth2Provider(OAuth2Provider):
    _validator = CustomOAuth2RequestValidator()


oauth2 = CustomOAuth2Provider()


@oauth2.invalid_response
def _invalid_response_handler(req):
    return api.abort(code=Unauthorized.code)
