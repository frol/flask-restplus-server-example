# encoding: utf-8
import pytest


@pytest.mark.parametrize('auth_scopes', (
    None,
    ('teams:write', ),
))
def test_getting_list_of_teams_by_unauthorized_user_must_fail(
        flask_app_client,
        regular_user,
        auth_scopes
):
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/teams/')

    assert response.status_code == 401
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


@pytest.mark.parametrize('auth_scopes', (
    ('teams:read', ),
    ('teams:read', 'teams:write', ),
))
def test_getting_list_of_teams_by_authorized_user(
        flask_app_client,
        regular_user,
        team_for_regular_user,
        auth_scopes
):
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/teams/')
    assert response.status_code == 200
    assert 'X-Total-Count' in response.headers
    assert int(response.headers['X-Total-Count']) == 1
    assert response.content_type == 'application/json'
    assert isinstance(response.json, list)
    assert set(response.json[0].keys()) >= {'id', 'title'}
    if response.json[0]['id'] == team_for_regular_user.id:
        assert response.json[0]['title'] == team_for_regular_user.title


@pytest.mark.parametrize('auth_scopes', (
    None,
    ('teams:write', ),
))
def test_getting_team_info_by_unauthorized_user_must_fail(
        flask_app_client,
        regular_user,
        team_for_regular_user,
        auth_scopes
):
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/teams/%d' % team_for_regular_user.id)

    assert response.status_code == 401
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


@pytest.mark.parametrize('auth_scopes', (
    ('teams:read', ),
    ('teams:read', 'teams:write', ),
))
def test_getting_team_info_by_authorized_user(
        flask_app_client,
        regular_user,
        team_for_regular_user,
        auth_scopes
):
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/teams/%d' % team_for_regular_user.id)

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'id', 'title'}
    assert response.json['id'] == team_for_regular_user.id
    assert response.json['title'] == team_for_regular_user.title


@pytest.mark.parametrize('auth_scopes', (
    None,
    ('teams:write', ),
))
def test_getting_list_of_team_members_by_unauthorized_user_must_fail(
        flask_app_client,
        regular_user,
        team_for_regular_user,
        auth_scopes
):
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/teams/%d/members/' % team_for_regular_user.id)

    assert response.status_code == 401
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


@pytest.mark.parametrize('auth_scopes', (
    ('teams:read', ),
    ('teams:read', 'teams:write', ),
))
def test_getting_list_of_team_members_by_authorized_user(
        flask_app_client,
        regular_user,
        team_for_regular_user,
        auth_scopes
):
    with flask_app_client.login(regular_user, auth_scopes=auth_scopes):
        response = flask_app_client.get('/api/v1/teams/%d/members/' % team_for_regular_user.id)

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, list)
    assert set(response.json[0].keys()) >= {'team', 'user', 'is_leader'}
    assert set(member['team']['id'] for member in response.json) == {team_for_regular_user.id}
    assert regular_user.id in set(member['user']['id'] for member in response.json)
