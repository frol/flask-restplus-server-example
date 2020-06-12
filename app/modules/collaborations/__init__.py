# encoding: utf-8
"""
Collaborations module
============
"""

from app.extensions.api import api_v1


def init_app(app, **kwargs):
    # pylint: disable=unused-argument,unused-variable
    """
    Init Collaborations module.
    """
    api_v1.add_oauth_scope('collaborations:read', 'Provide access to Collaborations details')
    api_v1.add_oauth_scope('collaborations:write', 'Provide write access to Collaborations details')

    # Touch underlying modules
    from . import models, resources

    api_v1.add_namespace(resources.api)