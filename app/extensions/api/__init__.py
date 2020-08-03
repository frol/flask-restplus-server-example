# -*- coding: utf-8 -*-
"""
API extension
=============
"""

from copy import deepcopy

from flask import Blueprint, current_app  # NOQA

from .api import Api  # NOQA
from .namespace import Namespace  # NOQA
from .http_exceptions import abort  # NOQA

import logging

log = logging.getLogger(__name__)


api_v1 = Api(  # pylint: disable=invalid-name
    version='1.0.0',
    title='Houston',
    description=(
        '\n'.join(
            [
                'This is the backend API documentation for the Houston server.',
                '',
                'The API features:',
                '* Self-documented RESTful API server using auto-generated OpenAPI specifications;',
                '* OAuth2 Password Flow (Resource Owner Password Credentials Grant) support;',
                '* Role-based permission system (it is also auto-documented);',
                '* PATCH method handled accordingly to RFC 6902;',
            ]
        )
    ),
)


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    # Prevent config variable modification with runtime changes
    api_v1.authorizations = deepcopy(app.config['AUTHORIZATIONS'])
