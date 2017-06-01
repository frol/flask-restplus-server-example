# encoding: utf-8
# pylint: disable=missing-docstring

import json

from app.modules.teams import models


def test_new_team_creation(flask_app_client, db, regular_user):
    # pylint: disable=invalid-name
    team_title = "Test Team Title"
    with flask_app_client.login(regular_user, auth_scopes=('teams:write', )):
        response = flask_app_client.post('/api/v1/teams/', data={'title': team_title})

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'id', 'title'}
    assert response.json['title'] == team_title

    # Cleanup
    team = models.Team.query.get(response.json['id'])
    assert team.title == team_title
    with db.session.begin():
        db.session.delete(team)

def test_new_team_first_member_is_creator(flask_app_client, db, regular_user):
    # pylint: disable=invalid-name
    team_title = "Test Team Title"
    with flask_app_client.login(
            regular_user,
            auth_scopes=('teams:write', 'teams:read')
        ):
        response = flask_app_client.post('/api/v1/teams/', data={'title': team_title})

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'id', 'title'}
    assert response.json['title'] == team_title
    assert len(response.json['members']) == 1
    assert response.json['members'][0]['user']['id'] == regular_user.id
    assert response.json['members'][0]['is_leader'] == True

    # Cleanup
    team = models.Team.query.get(response.json['id'])
    assert team.title == team_title
    with db.session.begin():
        db.session.delete(team)


def test_new_team_creation_with_invalid_data_must_fail(flask_app_client, regular_user):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('teams:write', )):
        response = flask_app_client.post('/api/v1/teams/', data={'title': ""})

    assert response.status_code == 409
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


def test_update_team_info(flask_app_client, regular_user, team_for_regular_user):
    # pylint: disable=invalid-name
    team_title = "Test Team Title"
    with flask_app_client.login(regular_user, auth_scopes=('teams:write', )):
        response = flask_app_client.patch(
            '/api/v1/teams/%d' % team_for_regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'replace',
                    'path': '/title',
                    'value': team_title
                },
            ])
        )

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'id', 'title'}
    assert response.json['id'] == team_for_regular_user.id
    assert response.json['title'] == team_title
    assert team_for_regular_user.title == team_title


def test_update_team_info_with_invalid_data_must_fail(
        flask_app_client,
        regular_user,
        team_for_regular_user
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('teams:write', )):
        response = flask_app_client.patch(
            '/api/v1/teams/%d' % team_for_regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'replace',
                    'path': '/title',
                    'value': '',
                },
            ])
        )

    assert response.status_code == 409
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


def test_update_team_info_without_value_must_fail(
        flask_app_client,
        regular_user,
        team_for_regular_user
):
    with flask_app_client.login(regular_user, auth_scopes=('teams:write', )):
        response = flask_app_client.patch(
            '/api/v1/teams/%d' % team_for_regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'replace',
                    'path': '/title',
                }
            ])
        )

    assert response.status_code == 422
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


def test_update_team_info_without_slash_in_path_must_fail(
        flask_app_client,
        regular_user,
        team_for_regular_user
):
    with flask_app_client.login(regular_user, auth_scopes=('teams:write',)):
        response = flask_app_client.patch(
            '/api/v1/teams/%d' % team_for_regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'replace',
                    'path': 'title',
                    'value': 'New Team Value',
                }
            ])
        )

    assert response.status_code == 422
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


def test_team_deletion(flask_app_client, regular_user, team_for_regular_user):
    with flask_app_client.login(regular_user, auth_scopes=('teams:write', )):
        response = flask_app_client.delete(
            '/api/v1/teams/%d' % team_for_regular_user.id
        )

    assert response.status_code == 204


def test_add_new_team_member(flask_app_client, db, regular_user, admin_user, team_for_regular_user):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('teams:write', )):
        response = flask_app_client.post(
            '/api/v1/teams/%d/members/' % team_for_regular_user.id,
            data={
                'user_id': admin_user.id,
            }
        )

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'team', 'user', 'is_leader'}
    assert response.json['team']['id'] == team_for_regular_user.id
    assert response.json['user']['id'] == admin_user.id

    # Cleanup
    team_members = models.TeamMember.query.filter_by(team=team_for_regular_user, user=admin_user)
    assert team_members.count() == 1
    with db.session.begin():
        team_members.delete()


def test_delete_team_member(
        flask_app_client, db, regular_user, readonly_user, team_for_regular_user
):
    # pylint: disable=invalid-name,unused-argument
    with flask_app_client.login(regular_user, auth_scopes=('teams:write', )):
        response = flask_app_client.delete(
            '/api/v1/teams/%d/members/%d' % (team_for_regular_user.id, readonly_user.id),
        )

    assert response.status_code == 200
    assert response.content_type == 'application/json'
