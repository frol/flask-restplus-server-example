# encoding: utf-8
import datetime
import pytest


@pytest.yield_fixture()
def regular_user_oauth2_client(regular_user ,db):
    # pylint: disable=invalid-name,unused-argument
    from app.modules.auth.models import OAuth2Client

    regular_user_oauth2_client_instance = OAuth2Client(
        user=regular_user,
        client_id='regular_user_client',
        client_secret='regular_user_secret',
        redirect_uris=[],
        default_scopes=[]
    )

    with db.session.begin():
        db.session.add(regular_user_oauth2_client_instance)

    yield regular_user_oauth2_client_instance

    with db.session.begin():
        db.session.delete(regular_user_oauth2_client_instance)


@pytest.yield_fixture()
def regular_user_oauth2_token(regular_user_oauth2_client, db):
    from app.modules.auth.models import OAuth2Token

    regular_user_token = OAuth2Token(
        client=regular_user_oauth2_client,
        user=regular_user_oauth2_client.user,
        access_token='test_token',
        refresh_token='test_refresh_token',
        expires=datetime.datetime.now() + datetime.timedelta(seconds=3600),
        token_type=OAuth2Token.TokenTypes.Bearer,
        scopes=[]
    )

    with db.session.begin():
        db.session.add(regular_user_token)

    yield regular_user_token

    with db.session.begin():
        db.session.delete(regular_user_token)
