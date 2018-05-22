# encoding: utf-8
"""
Auth module
===========
"""
from flask_login import current_user
from app.extensions.api import api_v1

def load_user_from_request(request):
    """
    Load user from OAuth2 Authentication header.
    """
    user = current_user

    return user

def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    Init auth module.
    """
    # Bind Flask-Login for current_user

    # Register OAuth scopes
    api_v1.add_oauth_scope('auth:read', "Provide access to auth details")
    api_v1.add_oauth_scope('auth:write', "Provide write access to auth details")

    # Touch underlying modules
    from . import models, views, resources  # pylint: disable=unused-variable

    # Mount authentication routes
    app.register_blueprint(views.auth_blueprint)
    api_v1.add_namespace(resources.api)
