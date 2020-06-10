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
import logging

from .views import DOCUMENTATION_STATIC_ROOT

log = logging.getLogger(__name__)

documentation_blueprint = Blueprint(
    'swagger-ui', __name__, static_folder=DOCUMENTATION_STATIC_ROOT,
)  # pylint: disable=invalid-name


@documentation_blueprint.route('/swaggerui/<path:path>', methods=['GET'])
def serve_swaggerui_static_assets(path, *args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint offers the home page html
    """
    if not current_app.debug:
        log.warninig('Swagger-UI files are recommended to be served by NGINX')

    return send_from_directory(documentation_blueprint.static_folder, path)
