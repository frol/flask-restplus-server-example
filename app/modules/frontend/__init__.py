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
    from . import views

    # Mount front-end routes
    app.register_blueprint(views.frontend_blueprint)

    app.register_blueprint(views.houston_blueprint)
