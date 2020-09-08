# -*- coding: utf-8 -*-
"""
Front-end module
================
"""

from app.extensions.api import api_v1


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    Init front-end module.
    """
    api_v1.add_oauth_scope('frontends:read', 'Provide access to Frontend details')
    api_v1.add_oauth_scope('frontends:write', 'Provide write access to Frontend details')

    # Touch underlying modules
    from . import views_backend, views_frontend, views_documentation

    # Mount front-end routes
    app.register_blueprint(views_frontend.frontend_blueprint)

    app.register_blueprint(views_backend.backend_blueprint)

    app.register_blueprint(views_documentation.documentation_blueprint)

    from . import resources  # NOQA

    api_v1.add_namespace(resources.api)
