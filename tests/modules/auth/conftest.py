# encoding: utf-8
import datetime
import pytest


@pytest.yield_fixture()
def regular_user_oauth2_client(regular_user, temp_db_instance_helper):
    # pylint: disable=invalid-name,unused-argument
    from app.modules.auth.models import OAuth2Client

    for _ in temp_db_instance_helper(
            OAuth2Client(
                user=regular_user,
                client_id='regular_user_client',
                client_secret='regular_user_secret',
                redirect_uris=[],
                default_scopes=['auth:read', 'auth:write']
            )
        ):
        yield _


@pytest.yield_fixture()
def regular_user_oauth2_token(regular_user_oauth2_client, temp_db_instance_helper):
    from app.modules.auth.models import OAuth2Token

    for _ in temp_db_instance_helper(
            OAuth2Token(
                client=regular_user_oauth2_client,
                user=regular_user_oauth2_client.user,
                access_token='test_token',
                refresh_token='test_refresh_token',
                expires=datetime.datetime.now() + datetime.timedelta(seconds=3600),
                token_type=OAuth2Token.TokenTypes.Bearer,
                scopes=regular_user_oauth2_client.default_scopes
            )
        ):
        yield _
