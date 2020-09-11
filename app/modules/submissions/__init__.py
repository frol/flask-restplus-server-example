# -*- coding: utf-8 -*-
"""
Submissions module
============
"""

from app.extensions.api import api_v1


def init_app(app, **kwargs):
    # pylint: disable=unused-argument,unused-variable
    """
    Init Submissions module.
    """
    api_v1.add_oauth_scope('submissions:read', 'Provide access to Submissions details')
    api_v1.add_oauth_scope('submissions:write', 'Provide write access to Submissions details')

    # Touch underlying modules
    from . import models, resources  # NOQA

    api_v1.add_namespace(resources.api)