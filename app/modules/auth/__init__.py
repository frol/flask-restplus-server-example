# -*- coding: utf-8 -*-
"""
Auth module
===========
"""
from app.extensions.api import api_v1


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    Init auth module.
    """
    # Register OAuth scopes
    api_v1.add_oauth_scope('auth:read', 'Provide access to auth details')
    api_v1.add_oauth_scope('auth:write', 'Provide write access to auth details')

    # Touch underlying modules
    from . import models, views, resources  # pylint: disable=unused-import  # NOQA

    # Mount authentication routes
    api_v1.add_namespace(resources.api)
