# encoding: utf-8
# pylint: disable=missing-docstring
import pytest
import six


@pytest.mark.parametrize('auth_scopes,redirect_uris', (
    (['auth:write'], ['http://1', 'http://2']),
    (['auth:write', 'auth:read'], None),
))
def test_creating_oauth2_client(
        flask_app_client, regular_user, db, auth_scopes, redirect_uris
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.post(
            '/api/v1/auth/oauth2_clients/',
            data={
                'redirect_uris': redirect_uris,
                'default_scopes': ['users:read', 'users:write', 'auth:read'],
            }
        )

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {
        'user_id',
        'client_id',
        'client_secret',
        'client_type',
        'default_scopes',
        'redirect_uris'
    }
    assert isinstance(response.json['client_id'], six.text_type)
    assert isinstance(response.json['client_secret'], six.text_type)
    assert isinstance(response.json['default_scopes'], list)
    assert set(response.json['default_scopes']) == {'users:read', 'users:write', 'auth:read'}
    assert isinstance(response.json['redirect_uris'], list)

    # Cleanup
    from app.modules.auth.models import OAuth2Client

    oauth2_client_instance = OAuth2Client.query.get(response.json['client_id'])
    assert oauth2_client_instance.client_secret == response.json['client_secret']

    db.session.delete(oauth2_client_instance)
    db.session.commit()


@pytest.mark.parametrize('auth_scopes', (
    [],
    ['auth:read'],
    ['auth:read', 'user:read'],
    ['user:read'],
))
def test_creating_oauth2_client_by_unauthorized_user_must_fail(
        flask_app_client, regular_user, auth_scopes
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.post(
            '/api/v1/auth/oauth2_clients/',
            data={
                'default_scopes': ['users:read', 'users:write', 'invalid'],
            }
        )

    assert response.status_code == 401
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


def test_creating_oauth2_client_must_fail_for_invalid_scopes(
        flask_app_client, regular_user
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=['auth:write']):
        response = flask_app_client.post(
            '/api/v1/auth/oauth2_clients/',
            data={
                'redirect_uris': [],
                'default_scopes': ['users:read', 'users:write', 'invalid'],
            }
        )

    assert response.status_code == 422
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}
