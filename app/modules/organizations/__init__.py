# -*- coding: utf-8 -*-
"""
Organizations module
============
"""

from app.extensions.api import api_v1


def init_app(app, **kwargs):
    # pylint: disable=unused-argument,unused-variable
    """
    Init Organizations module.
    """
    api_v1.add_oauth_scope(
        'organizations:read', 'Provide access to Organizations details'
    )
    api_v1.add_oauth_scope(
        'organizations:write', 'Provide write access to Organizations details'
    )

    # Touch underlying modules
    from . import models, resources  # NOQA

    api_v1.add_namespace(resources.api)
