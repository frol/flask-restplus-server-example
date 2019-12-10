# encoding: utf-8
# pylint: disable=missing-docstring
import json


def test_modifying_user_info_by_owner(flask_app_client, regular_user, db):
    # pylint: disable=invalid-name
    saved_middle_name = regular_user.middle_name
    with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
        response = flask_app_client.patch(
            '/api/v1/users/%d' % regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'test',
                    'path': '/current_password',
                    'value': regular_user.password_secret,
                },
                {
                    'op': 'replace',
                    'path': '/middle_name',
                    'value': "Modified Middle Name",
                },
            ])
        )

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'id', 'username'}
    assert response.json['id'] == regular_user.id
    assert 'password' not in response.json.keys()

    # Restore original state
    from app.modules.users.models import User

    user1_instance = User.query.get(response.json['id'])
    assert user1_instance.username == regular_user.username
    assert user1_instance.middle_name == "Modified Middle Name"

    user1_instance.middle_name = saved_middle_name
    with db.session.begin():
        db.session.merge(user1_instance)

def test_modifying_user_info_by_admin(flask_app_client, admin_user, regular_user, db):
    # pylint: disable=invalid-name
    saved_middle_name = regular_user.middle_name
    with flask_app_client.login(admin_user, auth_scopes=('users:write',)):
        response = flask_app_client.patch(
            '/api/v1/users/%d' % regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'test',
                    'path': '/current_password',
                    'value': admin_user.password_secret,
                },
                {
                    'op': 'replace',
                    'path': '/middle_name',
                    'value': "Modified Middle Name",
                },
                {
                    'op': 'replace',
                    'path': '/is_active',
                    'value': False,
                },
                {
                    'op': 'replace',
                    'path': '/is_regular_user',
                    'value': False,
                },
                {
                    'op': 'replace',
                    'path': '/is_admin',
                    'value': True,
                },
            ])
        )

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'id', 'username'}
    assert response.json['id'] == regular_user.id
    assert 'password' not in response.json.keys()

    # Restore original state
    from app.modules.users.models import User

    user1_instance = User.query.get(response.json['id'])
    assert user1_instance.username == regular_user.username
    assert user1_instance.middle_name == "Modified Middle Name"
    assert not user1_instance.is_active
    assert not user1_instance.is_regular_user
    assert user1_instance.is_admin

    user1_instance.middle_name = saved_middle_name
    user1_instance.is_active = True
    user1_instance.is_regular_user = True
    user1_instance.is_admin = False
    with db.session.begin():
        db.session.merge(user1_instance)

def test_modifying_user_info_admin_fields_by_not_admin(flask_app_client, regular_user, db):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
        response = flask_app_client.patch(
            '/api/v1/users/%d' % regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'test',
                    'path': '/current_password',
                    'value': regular_user.password_secret,
                },
                {
                    'op': 'replace',
                    'path': '/middle_name',
                    'value': "Modified Middle Name",
                },
                {
                    'op': 'replace',
                    'path': '/is_active',
                    'value': False,
                },
                {
                    'op': 'replace',
                    'path': '/is_regular_user',
                    'value': False,
                },
                {
                    'op': 'replace',
                    'path': '/is_admin',
                    'value': True,
                },
            ])
        )

    assert response.status_code == 403
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'status', 'message'}


def test_modifying_user_info_with_invalid_format_must_fail(flask_app_client, regular_user):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
        response = flask_app_client.patch(
            '/api/v1/users/%d' % regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'test',
                    'path': '/first_name',
                    'value': '',
                },
                {
                    'op': 'replace',
                    'path': '/middle_name',
                },
            ])
        )

    assert response.status_code == 422
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'status', 'message'}

def test_modifying_user_info_with_invalid_password_must_fail(flask_app_client, regular_user):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
        response = flask_app_client.patch(
            '/api/v1/users/%d' % regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'test',
                    'path': '/current_password',
                    'value': "invalid_password",
                },
                {
                    'op': 'replace',
                    'path': '/middle_name',
                    'value': "Modified Middle Name",
                },
            ])
        )

    assert response.status_code == 403
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'status', 'message'}

def test_modifying_user_info_with_conflict_data_must_fail(
        flask_app_client,
        admin_user,
        regular_user
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
        response = flask_app_client.patch(
            '/api/v1/users/%d' % regular_user.id,
            content_type='application/json',
            data=json.dumps([
                {
                    'op': 'test',
                    'path': '/current_password',
                    'value': regular_user.password_secret,
                },
                {
                    'op': 'replace',
                    'path': '/email',
                    'value': admin_user.email,
                },
            ])
        )

    assert response.status_code == 409
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'status', 'message'}
