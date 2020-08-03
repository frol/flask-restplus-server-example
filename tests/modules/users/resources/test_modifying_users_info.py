# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import json
import uuid


def test_modifying_user_info_by_owner(flask_app_client, regular_user, db):
    # pylint: disable=invalid-name
    try:
        saved_full_name = regular_user.full_name
        with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
            response = flask_app_client.patch(
                '/api/v1/users/%s' % regular_user.guid,
                content_type='application/json',
                data=json.dumps(
                    [
                        {
                            'op': 'test',
                            'path': '/current_password',
                            'value': regular_user.password_secret,
                        },
                        {
                            'op': 'replace',
                            'path': '/full_name',
                            'value': 'Modified Full Name',
                        },
                    ]
                ),
            )

        from app.modules.users.models import User

        temp_user = User.query.get(response.json['guid'])

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert isinstance(response.json, dict)
        assert set(response.json.keys()) >= {'guid', 'email'}
        assert uuid.UUID(response.json['guid']) == regular_user.guid
        assert 'password' not in response.json.keys()

        assert temp_user.email == regular_user.email
        assert temp_user.full_name == 'Modified Full Name'
    except Exception as ex:
        raise ex
    finally:
        # Restore original state
        regular_user.full_name = saved_full_name
        with db.session.begin():
            db.session.merge(regular_user)


def test_modifying_user_info_by_admin(flask_app_client, admin_user, regular_user, db):
    # pylint: disable=invalid-name
    try:
        saved_full_name = regular_user.full_name
        with flask_app_client.login(admin_user, auth_scopes=('users:write',)):
            response = flask_app_client.patch(
                '/api/v1/users/%s' % regular_user.guid,
                content_type='application/json',
                data=json.dumps(
                    [
                        {
                            'op': 'test',
                            'path': '/current_password',
                            'value': admin_user.password_secret,
                        },
                        {
                            'op': 'replace',
                            'path': '/full_name',
                            'value': 'Modified Full Name',
                        },
                        {'op': 'replace', 'path': '/is_active', 'value': False},
                        {'op': 'replace', 'path': '/is_staff', 'value': False},
                        {'op': 'replace', 'path': '/is_admin', 'value': True},
                    ]
                ),
            )

        from app.modules.users.models import User

        temp_user = User.query.get(response.json['guid'])

        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert isinstance(response.json, dict)
        assert set(response.json.keys()) >= {'guid', 'email'}
        assert uuid.UUID(response.json['guid']) == regular_user.guid
        assert 'password' not in response.json.keys()

        assert temp_user.email == regular_user.email
        assert temp_user.full_name == 'Modified Full Name'
        assert not temp_user.is_active
        assert not temp_user.is_staff
        assert temp_user.is_admin
    except Exception as ex:
        raise ex
    finally:
        # Restore original state
        regular_user.full_name = saved_full_name
        regular_user.is_active = True
        regular_user.is_staff = True
        regular_user.is_admin = False
        with db.session.begin():
            db.session.merge(regular_user)


def test_modifying_user_info_admin_fields_by_not_admin(
    flask_app_client, regular_user, db
):
    # pylint: disable=invalid-name
    try:
        saved_full_name = regular_user.full_name
        with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
            response = flask_app_client.patch(
                '/api/v1/users/%s' % regular_user.guid,
                content_type='application/json',
                data=json.dumps(
                    [
                        {
                            'op': 'test',
                            'path': '/current_password',
                            'value': regular_user.password_secret,
                        },
                        {
                            'op': 'replace',
                            'path': '/full_name',
                            'value': 'Modified Full Name',
                        },
                        {'op': 'replace', 'path': '/is_active', 'value': False},
                        {'op': 'replace', 'path': '/is_staff', 'value': False},
                        {'op': 'replace', 'path': '/is_admin', 'value': True},
                    ]
                ),
            )

        assert response.status_code == 403
        assert response.content_type == 'application/json'
        assert isinstance(response.json, dict)
        assert set(response.json.keys()) >= {'status', 'message'}
    except Exception as ex:
        raise ex
    finally:
        regular_user.full_name = saved_full_name
        regular_user.is_active = True
        regular_user.is_staff = True
        regular_user.is_admin = False
        with db.session.begin():
            db.session.merge(regular_user)


def test_modifying_user_info_with_invalid_format_must_fail(
    flask_app_client, regular_user
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
        response = flask_app_client.patch(
            '/api/v1/users/%s' % regular_user.guid,
            content_type='application/json',
            data=json.dumps(
                [
                    {'op': 'test', 'path': '/full_name', 'value': ''},
                    {'op': 'replace', 'path': '/website'},
                ]
            ),
        )

    assert response.status_code == 422
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'status', 'message'}


def test_modifying_user_info_with_invalid_password_must_fail(
    flask_app_client, regular_user
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
        response = flask_app_client.patch(
            '/api/v1/users/%s' % regular_user.guid,
            content_type='application/json',
            data=json.dumps(
                [
                    {
                        'op': 'test',
                        'path': '/current_password',
                        'value': 'invalid_password',
                    },
                    {
                        'op': 'replace',
                        'path': '/full_name',
                        'value': 'Modified Full Name',
                    },
                ]
            ),
        )

    assert response.status_code == 403
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'status', 'message'}


def test_modifying_user_info_with_conflict_data_must_fail(
    flask_app_client, admin_user, regular_user
):
    # pylint: disable=invalid-name
    with flask_app_client.login(regular_user, auth_scopes=('users:write',)):
        response = flask_app_client.patch(
            '/api/v1/users/%s' % regular_user.guid,
            content_type='application/json',
            data=json.dumps(
                [
                    {
                        'op': 'test',
                        'path': '/current_password',
                        'value': regular_user.password_secret,
                    },
                    {'op': 'replace', 'path': '/email', 'value': admin_user.email},
                ]
            ),
        )

    assert response.status_code == 409
    assert response.content_type == 'application/json'
    assert isinstance(response.json, dict)
    assert set(response.json.keys()) >= {'status', 'message'}
