from app.extensions import login_manager, oauth2

from . import models, views


def load_user_from_request(request):
    """
    Load user from OAuth2 Authentication header.
    """
    user = None
    if hasattr(request, 'oauth'):
        user = request.oauth.user
    else:
        is_valid, oauth = oauth2.verify_request([])
        if is_valid:
            user = oauth.user
    return user

def init_app(app, **kwargs):
    # Bind Flask-Login for current_user
    login_manager.request_loader(load_user_from_request)
    
    # Mount authentication routes 
    app.register_blueprint(views.auth_blueprint)
