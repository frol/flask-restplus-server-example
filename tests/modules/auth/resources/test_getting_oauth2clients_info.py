# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import pytest
import uuid


@pytest.mark.parametrize(
    'auth_scopes',
    (
        ['auth:read'],
        ['auth:read', 'auth:write'],
    ),
)
def test_getting_list_of_oauth2_clients_by_authorized_user(
    flask_app_client, regular_user, regular_user_oauth2_client, auth_scopes
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/auth/clients')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, list)
    assert set(response.json[0].keys()) >= {'guid'}
    assert uuid.UUID(response.json[0]['guid']) == regular_user_oauth2_client.guid


@pytest.mark.parametrize(
    'auth_scopes',
    (
        [],
        ['users:read'],
        ['auth:write'],
    ),
)
def test_getting_list_of_oauth2_clients_by_unauthorized_user_must_fail(
    flask_app_client, regular_user, auth_scopes
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/auth/clients')

    assert response.status_code == 401
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}
