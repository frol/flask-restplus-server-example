# pylint: disable=missing-docstring
import pytest

@pytest.mark.parametrize('path,status_code', (
    ('/api/v1/teams/', 401),
    ('/api/v1/users/1', 401),
))
def test_teams_options_unauthorized(path, status_code, flask_app_client):
    response = flask_app_client.options(path)

    assert response.status_code == status_code


@pytest.mark.parametrize('path,expected_allowed_methods', (
    ('/api/v1/teams/', {'GET', 'POST', 'OPTIONS'}),
    ('/api/v1/teams/1', {'GET', 'OPTIONS', 'PATCH', 'DELETE'}),
    ('/api/v1/teams/2', {'OPTIONS'}),
))
def test_teams_options_authorized(
        path,
        expected_allowed_methods,
        flask_app_client,
        regular_user,
        team_for_regular_user,
        team_for_nobody
    ):
    with flask_app_client.login(regular_user, auth_scopes=('teams:write', 'teams:read')):
        response = flask_app_client.options(path)

    assert response.status_code == 204
    assert set(response.headers['Allow'].split(', ')) == expected_allowed_methods


@pytest.mark.parametrize('http_path,expected_allowed_methods', (
    ('/api/v1/teams/', {'GET', 'POST', 'OPTIONS'}),
))
def test_preflight_options_request(http_path, expected_allowed_methods, flask_app_client):
    response = flask_app_client.open(
        method='OPTIONS',
        path=http_path,
        headers={'Access-Control-Request-Method': 'post'}
    )
    assert response.status_code == 200
    assert set(
        response.headers['Access-Control-Allow-Methods'].split(', ')
    ) == expected_allowed_methods
