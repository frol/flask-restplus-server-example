# encoding: utf-8
"""
Front-end module
================
"""


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    Init front-end module.
    """
    # Touch underlying modules
    from . import views_backend, views_frontend

    # Mount front-end routes
    app.register_blueprint(views_frontend.frontend_blueprint)

    app.register_blueprint(views_backend.backend_blueprint)
