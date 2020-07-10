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
from flask import Blueprint, request, flash, send_file
from flask_login import login_user, logout_user, login_required
import logging

from app.modules.users.models import User
from app.modules.assets.models import Asset

from app.modules.auth.views import (
    _url_for,
    _is_safe_url,
)

from .views import (
    HOUSTON_STATIC_ROOT,
    create_session_oauth2_token,
    delete_session_oauth2_token,
    _render_template,
)


log = logging.getLogger(__name__)

backend_blueprint = Blueprint(
    'backend', __name__, url_prefix='/houston', static_folder=HOUSTON_STATIC_ROOT,
)  # pylint: disable=invalid-name


@backend_blueprint.route('/', methods=['GET'])
def home(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint offers the home page
    """
    from app.version import version

    return _render_template('home.jinja2', version=version)


@backend_blueprint.route('/login', methods=['POST'])
def user_login(email=None, password=None, remember=None, *args, **kwargs):
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

    user = User.find(email=email, password=password)

    redirect = _url_for('backend.home')
    if user is not None:
        if True not in [user.in_alpha, user.in_beta, user.is_staff, user.is_admin]:
            flash(
                'Your login was correct, but Wildbook is in BETA at the moment and is invite-only.',
                'danger',
            )
            redirect = _url_for('backend.home')
        else:
            status = login_user(user, remember=remember)

            if status:
                # User logged in organically.
                log.info('Logged in User (remember = %s): %r' % (remember, user,))
                flash('Logged in successfully.', 'success')
                create_session_oauth2_token()

                redirect_ = flask.request.args.get('next')
                if redirect_ is not None and _is_safe_url(redirect_):
                    redirect = redirect_
            else:
                flash(
                    'We could not log you in, most likely due to your account being disabled.  Please speak to a staff member.',
                    'danger',
                )
                redirect = _url_for('backend.home')
    else:
        flash('Username or password unrecognized.', 'danger')
        redirect = _url_for('backend.home')

    return flask.redirect(redirect)


@backend_blueprint.route('/logout', methods=['GET'])
@login_required
def user_logout(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint is the landing page for the logged-in user
    """
    # Delete the Oauth2 token for this session
    delete_session_oauth2_token()
    logout_user()

    flash('You were successfully logged out.', 'warning')

    return flask.redirect(_url_for('backend.home'))


@backend_blueprint.route('/asset/<code>', methods=['GET'])
# @login_required
def asset(code, *args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint is the account page for the logged-in user
    """
    asset = Asset.query.filter_by(code=code).first_or_404()
    return send_file(asset.absolute_filepath, mimetype='image/jpeg')
