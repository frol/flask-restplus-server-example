# pylint: disable=missing-docstring
import pytest


@pytest.mark.parametrize('http_method,http_path', (
    ('GET', '/api/v1/teams/'),
    ('POST', '/api/v1/teams/'),
    ('GET', '/api/v1/teams/1'),
    ('PATCH', '/api/v1/teams/1'),
    ('DELETE', '/api/v1/teams/1'),
    ('GET', '/api/v1/teams/1/members/'),
    ('POST', '/api/v1/teams/1/members/'),
    ('DELETE', '/api/v1/teams/1/members/1'),
))
def test_unauthorized_access(http_method, http_path, flask_app_client):
    response = flask_app_client.open(method=http_method, path=http_path)
    assert response.status_code == 401
