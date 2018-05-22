# coding: utf-8
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""

from flask import Blueprint, request, render_template, session
from flask_login import current_user
from flask_restplus_patched._http import HTTPStatus
from authlib.specs.rfc6749 import OAuth2Error
from app.extensions import api, oauth2, db

from app.modules.users.models import User
from .models import OAuth2Client

auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')  # pylint: disable=invalid-name
#
# def current_user():
#     if 'id' in session:
#         uid = session['id']
#         return User.query.get(uid)
#     return None

@auth_blueprint.route('/oauth2/invalid_request', methods=['GET'])
def api_invalid_response(req):
    """
    This is a default handler for OAuth2Provider, which raises abort exception
    with error message in JSON format.
    """
    # pylint: disable=unused-argument
    api.abort(code=HTTPStatus.UNAUTHORIZED.value)


@auth_blueprint.route('/oauth2/token', methods=['GET', 'POST'])
def access_token(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint is for exchanging/refreshing an access token.

    Returns:
        token response
    """
    # with db.session.begin():
    response = oauth2.create_token_response()

    return response


@auth_blueprint.route('/oauth2/revoke', methods=['POST'])
def revoke_token():
    """
    This endpoint allows a user to revoke their access token.
    """
    with db.session.begin():
        response = oauth2.create_endpoint_response('revocation')
    return response


@auth_blueprint.route('/oauth2/authorize', methods=['GET', 'POST'])
def authorize(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint asks user if he grants access to his data to the requesting
    application.
    """
    # TODO: improve implementation. This implementation is broken because we
    # don't use cookies, so there is no session which client could carry on.
    # OAuth2 server should probably be deployed on a separate domain, so we
    # can implement a login page and store cookies with a session id.
    # ALTERNATIVELY, authorize page can be implemented as SPA (single page
    # application)
    from flask_login import login_user

    user = current_user()
    if request.method == 'GET':
        try:
            grant = oauth2.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            return error.error
        return render_template('authorize.html', user=user, grant=grant)
    if not user and 'username' in request.form:
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.find_with_password(username, password)
        if user:
            login_user(user)

    if request.form['confirm']:
        grant_user = user
    else:
        grant_user = None
    with db.session.begin():
        response = oauth2.create_authorization_response(grant_user=grant_user)

    return response or None
