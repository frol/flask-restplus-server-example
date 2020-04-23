# coding: utf-8
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""
import flask
from flask import Blueprint, request, render_template, url_for, flash, session, current_app, send_file
from flask_login import current_user, login_user, logout_user, login_required
import logging
from urllib.parse import urlparse, urljoin

from app.extensions import db, login_manager, oauth2

from app.modules.users.models import User
from app.modules.assets.models import Asset

import datetime
import pytz

import os

log = logging.getLogger(__name__)

PST = pytz.timezone('US/Pacific')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

HOUSTON_STATIC_ROOT = os.path.join(PROJECT_ROOT, 'app', 'static')

FRONTEND_STATIC_ROOT = os.path.join(HOUSTON_STATIC_ROOT, 'dist-latest')

frontend_blueprint = Blueprint('frontend', __name__, url_prefix='/', static_url_path='', static_folder=FRONTEND_STATIC_ROOT)          # pylint: disable=invalid-name

houston_blueprint  = Blueprint('houston',  __name__, url_prefix='/houston', static_url_path='/static', static_folder=HOUSTON_STATIC_ROOT)  # pylint: disable=invalid-name


def _render_template(template, **kwargs):
    now = datetime.datetime.now(tz=PST)
    config = {
        'base_url'             : current_app.config.get('BASE_URL'),
        'google_analytics_tag' : current_app.config.get('GOOGLE_ANALYTICS_TAG'),
        'stripe_public_key'    : current_app.config.get('STRIPE_PUBLIC_KEY'),
        'year'                 : now.year,
        'cachebuster'          : '20200322-0',
    }
    config.update(kwargs)
    return render_template(template, **config)


def _url_for(value, *args, **kwargs):
    kwargs['_external'] = 'https'
    kwargs['_scheme'] = 'https'
    return url_for(value, *args, **kwargs)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@login_manager.request_loader
def load_user_from_request(request):
    """
    Load user from OAuth2 Authentication header.
    """
    user = None
    if hasattr(request, 'oauth'):
        user = request.oauth.user
    else:
        is_valid, oauth = oauth2.verify_request(scopes=[])
        if is_valid:
            user = oauth.user
    return user


@login_manager.user_loader
def load_user(username):
    user = User.find(username=username)
    return user


@login_manager.unauthorized_handler
def unauthorized():
    flash(
        'You tried to load an unauthorized page.',
        'danger'
    )
    return flask.redirect(_url_for('frontend.home'))


def create_session_oauth2_token(cleanup_tokens=False, check_renewal=False):
    from app.extensions import db
    from app.modules.auth.models import OAuth2Client, OAuth2Token
    from app.extensions.api import api_v1
    from werkzeug import security
    import datetime

    if not current_user.is_authenticated:
        return None

    default_scopes = list(api_v1.authorizations['oauth2_password']['scopes'].keys())

    # Retrieve Oauth2 client for user and/or clean-up multiple clients
    session_oauth2_clients = OAuth2Client.query.filter_by(user=current_user, client_type=OAuth2Client.ClientTypes.confidential).all()
    session_oauth2_client = None
    if len(session_oauth2_clients) == 1:
        # We have an existing Oauth2 frontend client for this user, let's re-use it
        session_oauth2_client = session_oauth2_clients[0]
    elif len(session_oauth2_clients) > 1:
        # We have somehow created multiple clients for this user, delete them all and make new ones
        with db.session.begin():
            for session_oauth2_client_ in session_oauth2_clients:
                db.session.delete(session_oauth2_client_)

    if session_oauth2_client is None:
        session_oauth2_client = OAuth2Client(
            client_id='_session_oauth2_%s' % current_user.username,
            client_secret=security.gen_salt(50),
            client_type=OAuth2Client.ClientTypes.confidential,
            user=current_user,
            default_scopes=default_scopes
        )
        with db.session.begin():
            db.session.add(session_oauth2_client)
    log.info('Using session Oauth2 client = %r' % (session_oauth2_client, ))

    # Clean-up all tokens for the confidential client
    session_oauth2_bearer_tokens = OAuth2Token.query.filter_by(client=session_oauth2_client).all()
    log.info('User %s has %d confidential Oauth2 bearer tokens' % (current_user.username, len(session_oauth2_bearer_tokens), ))
    if cleanup_tokens:
        for session_oauth2_bearer_token_ in session_oauth2_bearer_tokens:
            session_oauth2_bearer_token_.delete()

    # IMPORTANT: WE NEED THIS TO BE IN UTC FOR OAUTH2
    expires = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(days=1)

    # Create a Oauth2 session bearer token with all scopes for this session
    session_oauth2_bearer_token = OAuth2Token(
        client=session_oauth2_client,
        user=current_user,
        token_type='Bearer',
        access_token=security.gen_salt(32),
        scopes=default_scopes,
        expires=expires
    )
    with db.session.begin():
        db.session.add(session_oauth2_bearer_token)

    # Add the access token to the session
    session_oauth2_access_token = session_oauth2_bearer_token.access_token
    session['access_token'] = session_oauth2_access_token


def check_session_oauth2_token(autorenew=True):
    from app.modules.auth.models import OAuth2Token

    if not current_user.is_authenticated:
        return False

    session_oauth2_access_token = session.get('access_token', None)
    if session_oauth2_access_token is None:
        return False

    session_oauth2_bearer_token = OAuth2Token.find(access_token=session_oauth2_access_token)
    if session_oauth2_bearer_token is None:
        if autorenew:
            create_session_oauth2_token()
            return True
        else:
            return False

    if session_oauth2_bearer_token.is_expired:
        if autorenew:
            create_session_oauth2_token()
            return True
        else:
            return False

    return None


def delete_session_oauth2_token():
    from app.modules.auth.models import OAuth2Token
    session_oauth2_access_token = session.get('access_token', None)
    if session_oauth2_access_token is not None:
        session_oauth2_bearer_token = OAuth2Token.find(access_token=session_oauth2_access_token)
        log.info('Deleting bearer token %r for user %r' % (session_oauth2_bearer_token, current_user.username), )
        if session_oauth2_bearer_token is not None:
            session_oauth2_bearer_token.delete()


@frontend_blueprint.route('/', methods=['GET'])
def root(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint offers the home page html
    """
    return frontend_blueprint.send_static_file('index.html')


@houston_blueprint.route('/', methods=['GET'])
def home(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint offers the home page html
    """
    from app.version import version
    return _render_template('home.html', version=version)


@houston_blueprint.route('/login', methods=['POST'])
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
        # log.info('request.form.remember = %r' % (remember, ))
        remember = remember in ['true', 'on']

    user = User.find(email=email, password=password)

    redirect = _url_for('frontend.account')
    if user is not None:
        if False:  # True not in [user.in_beta, user.is_staff, user.is_admin]:
            flash('Your login was correct, but Wildbook is in BETA at the moment and is invite-only.  Please call us at (949) 786-9625 and ask for an invite code.', 'danger')
            redirect = _url_for('frontend.home')
        else:
            status = login_user(user, remember=remember)

            if status:
                # User logged in organically.  No matter the reason, they should no longer be in account recovery
                user.in_reset = False
                with db.session.begin():
                    db.session.merge(user)
                db.session.refresh(user)
                assert not user.in_reset

                log.info('Logged in User (remember = %s): %r' % (remember, user, ))
                flash('Logged in successfully.', 'success')
                create_session_oauth2_token()

                redirect_ = flask.request.args.get('next')
                if redirect_ is not None and is_safe_url(redirect_):
                        redirect = redirect_
            else:
                flash('We could not log you in, most likely due to your account being disabled.  Please speak to a staff member.', 'danger')
                redirect = _url_for('frontend.home')
    else:
        flash('Username or password unrecognized.', 'danger')
        redirect = _url_for('frontend.home')

    return flask.redirect(redirect)


@houston_blueprint.route('/logout', methods=['GET'])
@login_required
def user_logout(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint is the landing page for the logged-in user
    """
    # Delete the Oauth2 token for this session
    delete_session_oauth2_token()
    logout_user()

    flash(
        'You were successfully logged out.',
        'warning'
    )

    return flask.redirect(_url_for('frontend.home'))


@houston_blueprint.route('/asset/<code>', methods=['GET'])
# @login_required
def asset(code, *args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint is the account page for the logged-in user
    """
    asset = Asset.query.filter_by(code=code).first_or_404()
    return send_file(asset.absolute_filepath, mimetype='image/jpeg')
