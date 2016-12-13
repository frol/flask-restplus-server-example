# coding: utf-8
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""

from flask import Blueprint, request, render_template
from flask_login import current_user
from flask_restplus_patched._http import HTTPStatus

from app.extensions import api, oauth2

from .models import OAuth2Client


auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')  # pylint: disable=invalid-name


@auth_blueprint.route('/oauth2/token', methods=['GET', 'POST'])
@oauth2.token_handler
def access_token(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint is for exchanging/refreshing an access token.

    Returns:
        response (dict): a dictionary or None as the extra credentials for
        creating the token response.
    """
    return None

@auth_blueprint.route('/oauth2/revoke', methods=['POST'])
@oauth2.revoke_handler
def revoke_token():
    """
    This endpoint allows a user to revoke their access token.
    """
    pass

@auth_blueprint.route('/oauth2/authorize', methods=['GET', 'POST'])
@oauth2.authorize_handler
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
    if not current_user.is_authenticated:
        return api.abort(code=HTTPStatus.UNAUTHORIZED)

    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        oauth2_client = OAuth2Client.query.get_or_404(client_id=client_id)
        kwargs['client'] = oauth2_client
        kwargs['user'] = current_user
        # TODO: improve template design
        return render_template('authorize.html', **kwargs)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'
