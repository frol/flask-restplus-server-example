# -*- coding: utf-8 -*-
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""
from flask import Blueprint, send_from_directory, current_app
import werkzeug
import logging

from .views import FRONTEND_STATIC_ROOT

log = logging.getLogger(__name__)

frontend_blueprint = Blueprint(
    'frontend', __name__, static_folder=FRONTEND_STATIC_ROOT,
)  # pylint: disable=invalid-name


@frontend_blueprint.route('/', defaults={'path': None}, methods=['GET'])
@frontend_blueprint.route('/<path:path>', methods=['GET'])
def serve_frontent_static_assets(path=None, *args, **kwargs):
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
        return serve_frontent_static_assets(path=None, *args, **kwargs)


@frontend_blueprint.errorhandler(404)
def page_not_found(event):
    log.error('Handled 404')
    # note that we set the 404 status explicitly
    return serve_frontent_static_assets('404.html'), 404
