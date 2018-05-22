from flask import g
from flask.sessions import SecureCookieSessionInterface
from flask_login import user_loaded_from_header
from flask_login import LoginManager as OriginalLoginManager

class CustomSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""
    def save_session(self, *args, **kwargs):
        if g.get('login_via_header'):
            return
        return super(CustomSessionInterface, self).save_session(*args,
                                                                **kwargs)


@user_loaded_from_header.connect
def user_loaded_from_header(self, user=None):
    g.login_via_header = True


class LoginManager(OriginalLoginManager):
    def init_app(self, app):
        app.session_interface = CustomSessionInterface()
        super().init_app(app)


