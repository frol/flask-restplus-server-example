# encoding: utf-8
"""
Application Users management related tasks for Invoke.
"""

from getpass import getpass

from ._utils import app_context_task


@app_context_task
def create_user(
        context,
        username,
        email,
        is_internal=False,
        is_admin=False,
        is_regular_user=True,
        is_active=True
    ):
    """
    Create a new user.
    """
    from app.modules.users.models import User

    password = getpass("Enter password: ")

    new_user = User(
        username=username,
        password=password,
        email=email,
        is_internal=is_internal,
        is_admin=is_admin,
        is_regular_user=is_regular_user,
        is_active=is_active
    )

    from app.extensions import db
    with db.session.begin():
        db.session.add(new_user)



@app_context_task
def create_oauth2_client(
        context,
        username,
        client_id,
        client_secret,
        default_scopes=None
    ):
    """
    Create a new OAuth2 Client associated with a given user (username).
    """
    from app.modules.users.models import User
    from app.modules.auth.models import OAuth2Client

    user = User.query.filter(User.username == username).first()
    if not user:
        raise Exception("User with username '%s' does not exist." % username)

    if default_scopes is None:
        from app.extensions.api import api_v1
        default_scopes = list(api_v1.authorizations['oauth2_password']['scopes'].keys())

    oauth2_client = OAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        user=user,
        default_scopes=default_scopes
    )

    from app.extensions import db
    with db.session.begin():
        db.session.add(oauth2_client)
