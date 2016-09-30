# pylint: disable=missing-docstring
import pytest

@pytest.mark.parametrize('path,status_code,expected_allowed_methods', (
    ('/api/v1/users/', 204, {'POST', 'OPTIONS'}),
    ('/api/v1/users/1', 401, None),
))
def test_users_options_unauthorized(path, status_code, expected_allowed_methods, flask_app_client):
    response = flask_app_client.options(path)

    assert response.status_code == status_code
    if expected_allowed_methods:
        assert set(response.headers['Allow'].split(', ')) == expected_allowed_methods


@pytest.mark.parametrize('path,expected_allowed_methods', (
    ('/api/v1/users/', {'POST', 'OPTIONS'}),
    ('/api/v1/users/1', {'GET', 'OPTIONS', 'PATCH'}),
    ('/api/v1/users/2', {'OPTIONS'}),
))
def test_users_options_authorized(path, expected_allowed_methods, flask_app_client, regular_user):
    with flask_app_client.login(regular_user, auth_scopes=('users:write', 'users:read')):
        response = flask_app_client.options(path)

    assert response.status_code == 204
    assert set(response.headers['Allow'].split(', ')) == expected_allowed_methods
