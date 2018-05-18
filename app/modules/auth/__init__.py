# encoding: utf-8
"""
Auth module
===========
"""
from app.extensions.api import api_v1


def load_user_from_request(request):
    """
    Load user from OAuth2 Authentication header.
    """
    from authlib.flask.oauth2 import current_token
    from app.modules.users.models import User
    if current_token:
        user_id = current_token.user_id
        if user_id:
            return User.query.get(user_id)
        elif current_token.user:
            return current_token.user
    return None


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    Init auth module.
    """
    # Bind Flask-Login for current_user
    from app.extensions import login_manager

    login_manager.request_loader(load_user_from_request)

    # Register OAuth scopes
    api_v1.add_oauth_scope('auth:read', "Provide access to auth details")
    api_v1.add_oauth_scope('auth:write', "Provide write access to auth details")

    # Touch underlying modules
    from . import models2, views, resources  # pylint: disable=unused-variable

    # Mount authentication routes
    app.register_blueprint(views.auth_blueprint)
    api_v1.add_namespace(resources.api)
