# -*- coding: utf-8 -*-
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""

from urllib.parse import urlparse, urljoin

import flask
from flask import request, url_for, flash

from app.extensions import login_manager, oauth2

from app.modules.users.models import User


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
def load_user(guid):
    user = User.query.filter(User.guid == guid).first()
    return user


@login_manager.unauthorized_handler
def unauthorized():
    flash('You tried to load an unauthorized page.', 'danger')
    return flask.redirect(_url_for('frontend.home'))
