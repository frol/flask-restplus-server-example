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
from flask import request, render_template, url_for, flash, session, current_app
from flask_login import current_user
import logging
from urllib.parse import urlparse, urljoin

from app.extensions import login_manager, oauth2

from app.modules.users.models import User

import datetime
import pytz
import os

log = logging.getLogger(__name__)

PST = pytz.timezone('US/Pacific')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

HOUSTON_STATIC_ROOT = os.path.join(PROJECT_ROOT, 'app', 'static')

FRONTEND_STATIC_ROOT = os.path.join(HOUSTON_STATIC_ROOT, 'dist-latest')


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


def _is_safe_url(target):
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
