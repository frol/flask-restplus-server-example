# encoding: utf-8
"""
Auth module
===========
"""
from app.extensions.api import api_v1


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    Init email module.
    """
    # Register OAuth scopes
    api_v1.add_oauth_scope('emails:read', "Provide access to email details")
    api_v1.add_oauth_scope('emails:write', "Provide write access to email details")

    # Touch underlying modules
    from . import models  # pylint: disable=unused-import  # NOQA
