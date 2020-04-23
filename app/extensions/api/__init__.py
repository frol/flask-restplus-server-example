# encoding: utf-8
"""
API extension
=============
"""

from copy import deepcopy

from flask import Blueprint, current_app

from .api import Api
from .namespace import Namespace
from .http_exceptions import abort

import logging

log = logging.getLogger(__name__)


api_v1 = Api( # pylint: disable=invalid-name
    version='1.0.0',
    title="Houston",
    description=(
        '\n'.join([
            'This is the backend API documentation for the Houston server.',
            '',
            'The API features:',
            '* Self-documented RESTful API server using auto-generated OpenAPI specifications;',
            '* OAuth2 Password Flow (Resource Owner Password Credentials Grant) support;',
            '* Role-based permission system (it is also auto-documented);',
            '* PATCH method handled accordingly to RFC 6902;',
        ])
    ),
)


def serve_swaggerui_assets(path):
    """
    Swagger-UI assets serving route.
    """
    from flask import send_from_directory

    if not current_app.debug:
        import warnings
        warnings.warn(
            "/swaggerui/ is recommended to be served by public-facing server (e.g. NGINX)"
        )

    static_root = current_app.config['STATIC_ROOT']
    return send_from_directory(static_root, path)


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    app.route('/swaggerui/<path:path>')(serve_swaggerui_assets)

    # Prevent config variable modification with runtime changes
    api_v1.authorizations = deepcopy(app.config['AUTHORIZATIONS'])
