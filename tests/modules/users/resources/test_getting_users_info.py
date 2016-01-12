# encoding: utf-8
# pylint: disable=missing-docstring
import pytest


@pytest.mark.parametrize('auth_scopes', (
    ('users:write', ),
    ('users:read', ),
    ('users:read', 'users:write', ),
))
def test_getting_list_of_users_by_unauthorized_user_must_fail(
        flask_app_client,
        regular_user,
        auth_scopes
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/users/')

    if 'users:read' in auth_scopes:
        assert response.status_code == 403
    else:
        assert response.status_code == 401
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}

@pytest.mark.parametrize('auth_scopes', (
    ('users:read', ),
    ('users:read', 'users:write', ),
))
def test_getting_list_of_users_by_authorized_user(flask_app_client, admin_user, auth_scopes):
    # pylint: disable=invalid-name
    with flask_app_client.login(admin_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/users/')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, list)
    assert set(response.json[0].keys()) >= {'id', 'username'}

def test_getting_user_info_by_unauthorized_user(flask_app_client, regular_user, admin_user):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:read',)):
        response = flask_app_client.get('/api/v1/users/%d' % admin_user.id)

    assert response.status_code == 403
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'status', 'message'}

def test_getting_user_info_by_authorized_user(flask_app_client, regular_user, admin_user):
    # pylint: disable=invalid-name
    with flask_app_client.login(admin_user, auth_scopes=('users:read',)):
        response = flask_app_client.get('/api/v1/users/%d' % regular_user.id)

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'id', 'username'}
    assert 'password' not in response.json.keys()

def test_getting_user_info_by_owner(flask_app_client, regular_user):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:read',)):
        response = flask_app_client.get('/api/v1/users/%d' % regular_user.id)

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'id', 'username'}
    assert 'password' not in response.json.keys()

def test_getting_user_me_info(flask_app_client, regular_user):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:read',)):
        response = flask_app_client.get('/api/v1/users/me')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'id', 'username'}
    assert 'password' not in response.json.keys()
