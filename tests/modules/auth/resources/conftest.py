# encoding: utf-8
import pytest


@pytest.yield_fixture(scope='session')
def regular_user_oauth2_client(regular_user):
    # pylint: disable=invalid-name,unused-argument
    from app.extensions import db
    from app.modules.auth.models import OAuth2Client

    admin_oauth2_client_instance = OAuth2Client(
        user=regular_user,
        client_id='regular_user_client',
        client_secret='regular_user_secret',
        redirect_uris=[],
        default_scopes=[]
    )

    db.session.add(admin_oauth2_client_instance)
    db.session.commit()
    yield admin_oauth2_client_instance
    db.session.delete(admin_oauth2_client_instance)
    db.session.commit()
