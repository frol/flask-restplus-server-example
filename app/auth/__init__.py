from . import models, views, providers


def load_user_from_request(request):
    """
    Load user from OAuth2 Authentication header.
    """
    user = None
    if hasattr(request, 'oauth'):
        user = request.oauth.user
    else:
        is_valid, oauth = providers.oauth2.verify_request([])
        if is_valid:
            user = oauth.user
    return user

def init_app(app, login_manager):
    # Bind Flask-Login for current_user
    login_manager.request_loader(load_user_from_request)
    
    # Bind Flask-oauthlib for OAuth2 authentication
    providers.oauth2.init_app(app)
    
    # Mount authentication routes 
    app.register_blueprint(views.auth_blueprint)
