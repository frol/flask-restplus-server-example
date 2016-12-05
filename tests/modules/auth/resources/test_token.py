from base64 import b64encode

import pytest


def test_regular_user_can_retrieve_token(
        flask_app_client,
        regular_user,
        regular_user_oauth2_client
    ):
    response = flask_app_client.post(
        '/auth/oauth2/token',
        content_type='application/x-www-form-urlencoded',
        data={
            'username': regular_user.username,
            'password': 'regular_user_password',
            'client_id': regular_user_oauth2_client.client_id,
            'client_secret': regular_user_oauth2_client.client_secret,
            'grant_type': 'password',
        },
    )

    assert response.status_code == 200
    assert set(response.json.keys()) >= {'access_token', 'refresh_token'}


def test_regular_user_cant_retrieve_token_without_credentials(
        flask_app_client,
        regular_user,
    ):
    response = flask_app_client.post(
        '/auth/oauth2/token',
        content_type='application/x-www-form-urlencoded',
        data={
            'username': regular_user.username,
            'password': 'regular_user_password',
            'grant_type': 'password',
        },
    )

    assert response.status_code == 401


def test_regular_user_cant_retrieve_token_with_invalid_credentials(
        flask_app_client,
        regular_user,
    ):
    response = flask_app_client.post(
        '/auth/oauth2/token',
        content_type='application/x-www-form-urlencoded',
        data={
            'username': regular_user.username,
            'password': 'wrong_password',
            'client_id': 'wrong_client_id',
            'client_secret': 'wrong_client_secret',
            'grant_type': 'password',
        },
    )

    assert response.status_code == 401


def test_regular_user_cant_retrieve_token_without_any_data(
        flask_app_client,
    ):
    response = flask_app_client.post(
        '/auth/oauth2/token',
        content_type='application/x-www-form-urlencoded',
        data={},
    )

    assert response.status_code == 400


def test_regular_user_can_refresh_token(
        flask_app_client,
        regular_user_oauth2_token,
    ):
    refresh_token_response = flask_app_client.post(
        '/auth/oauth2/token',
        content_type='application/x-www-form-urlencoded',
        data={
            'refresh_token': regular_user_oauth2_token.refresh_token,
            'client_id': regular_user_oauth2_token.client.client_id,
            'client_secret': regular_user_oauth2_token.client.client_secret,
            'grant_type': 'refresh_token',
        },
    )

    assert refresh_token_response.status_code == 200
    assert set(refresh_token_response.json.keys()) >= {'access_token'}


def test_regular_user_cant_refresh_token_with_invalid_refresh_token(
        flask_app_client,
        regular_user_oauth2_token,
    ):
    refresh_token_response = flask_app_client.post(
        '/auth/oauth2/token',
        content_type='application/x-www-form-urlencoded',
        data={
            'refresh_token': 'wrong_refresh_token',
            'client_id': regular_user_oauth2_token.client.client_id,
            'client_secret': regular_user_oauth2_token.client.client_secret,
            'grant_type': 'refresh_token',
        },
    )

    assert refresh_token_response.status_code == 401


def test_user_cant_refresh_token_without_any_data(
        flask_app_client,
    ):
    refresh_token_response = flask_app_client.post(
        '/auth/oauth2/token',
        content_type='application/x-www-form-urlencoded',
        data={},
    )

    assert refresh_token_response.status_code == 400


# There is a bug in flask-oauthlib: https://github.com/lepture/flask-oauthlib/issues/233
@pytest.mark.xfail
def test_regular_user_can_revoke_token(
        flask_app_client,
        regular_user_oauth2_token,
    ):
    data = {
        'token': regular_user_oauth2_token.refresh_token,
        'client_id': regular_user_oauth2_token.client.client_id,
        'client_secret': regular_user_oauth2_token.client.client_secret,
    }
    revoke_token_response = flask_app_client.post(
        '/auth/oauth2/revoke',
        content_type='application/x-www-form-urlencoded',
        headers={
            'Authorization': 'Basic %s' % b64encode(('%s:%s' % (regular_user_oauth2_token.client.client_id, regular_user_oauth2_token.client.client_secret)).encode('utf-8')),
        },
        data=data,
    )

    assert revoke_token_response.status_code == 200
