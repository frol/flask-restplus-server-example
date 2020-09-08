# -*- coding: utf-8 -*-
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""
import flask
from flask import Blueprint, send_from_directory, current_app, request
from flask_login import login_user, logout_user, login_required, current_user
import werkzeug
import logging

from app.modules.users.models import User

from app.modules.auth.views import (
    _url_for,
    _is_safe_url,
)

from .views import (
    FRONTEND_STATIC_ROOT,
    create_session_oauth2_token,
    delete_session_oauth2_token,
)

log = logging.getLogger(__name__)

frontend_blueprint = Blueprint(
    'frontend', __name__, static_folder=FRONTEND_STATIC_ROOT,
)  # pylint: disable=invalid-name


@frontend_blueprint.route('/', defaults={'path': None}, methods=['GET'])
@frontend_blueprint.route('/<path:path>', methods=['GET'])
def home(path=None, *args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint offers the home page html
    """
    if not current_app.debug:
        log.warning('Front-end files are recommended to be served by NGINX')

    if path is None:
        path = 'index.html'
    try:
        return send_from_directory(frontend_blueprint.static_folder, path)
    except werkzeug.exceptions.NotFound:
        return home(path=None, *args, **kwargs)


@frontend_blueprint.route('/login', methods=['POST'])
def referral_login(email=None, password=None, remember=None, refer=None, *args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint is the landing page for the logged-in user
    """
    if email is None:
        email = request.form.get('email', None)
    if password is None:
        password = request.form.get('password', None)
    if remember is None:
        remember = request.form.get('remember', None)
        remember = remember in ['true', 'on']
    if refer is None:
        refer = flask.request.args.get('next', request.form.get('next', None))

    if refer in ['origin']:
        refer = request.referrer

    if refer is not None:
        if not _is_safe_url(refer):
            log.error('User gave insecure next URL: %r' % (refer,))
            refer = None

    failure_refer = 'frontend.home'

    user = User.find(email=email, password=password)

    redirect = _url_for(failure_refer)
    if user is not None:
        if True not in [user.in_alpha, user.in_beta, user.is_staff, user.is_admin]:
            log.warning('User %r had a valid login, but is not a staff or beta member.',)
            redirect = _url_for(failure_refer)
        else:
            status = login_user(user, remember=remember)

            if status:
                # User logged in organically.
                log.info('Logged in User (remember = %s): %r' % (remember, user,))
                create_session_oauth2_token()

                if refer is not None:
                    log.info('Sending user to requested next: %r' % (refer,))
                    redirect = refer
            else:
                log.warning('Username or password unrecognized.')
                redirect = _url_for(failure_refer)
    else:
        log.warning('Username or password unrecognized.')
        redirect = _url_for(failure_refer)

    return flask.redirect(redirect)


@frontend_blueprint.route('/logout', methods=['POST'])
@login_required
def referral_logout(refer=None, *args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint is the landing page for the logged-in user
    """
    if refer is None:
        refer = flask.request.args.get('next', request.form.get('next', None))

    if refer in ['origin']:
        refer = request.referrer

    if refer is not None:
        if not _is_safe_url(refer):
            log.error('User gave insecure next URL: %r' % (refer,))
            refer = None

    # Delete the Oauth2 token for this session
    log.info('Logging out User: %r' % (current_user,))

    delete_session_oauth2_token()

    logout_user()

    if refer is None:
        redirect = _url_for('frontend.home')
    else:
        redirect = refer

    return flask.redirect(redirect)


@frontend_blueprint.errorhandler(404)
def page_not_found(event):
    log.error('Handled 404')
    # note that we set the 404 status explicitly
    return home('404.html'), 404
