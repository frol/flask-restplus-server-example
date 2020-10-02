# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import uuid
import config


def test_recaptcha(flask_app_client):
    response = flask_app_client.get('/api/v1/auth/recaptcha')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) == {'recaptcha_public_key'}
    assert (
        response.json['recaptcha_public_key'] == config.TestingConfig.RECAPTCHA_PUBLIC_KEY
    )


def create_new_user(flask_app_client, data, must_succeed=True):
    """
    Helper function for valid new user creation.
    """
    _data = {
        'recaptcha_key': config.TestingConfig.RECAPTCHA_BYPASS,
    }
    _data.update(data)
    response = flask_app_client.post('/api/v1/users/', data=_data)

    if must_succeed:
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert set(response.json.keys()) >= {'guid', 'email'}
        return uuid.UUID(response.json['guid'])
    return response


def test_new_user_creation(patch_User_password_scheme, flask_app_client, db):
    # pylint: disable=invalid-name,unused-argument
    user_guid = create_new_user(
        flask_app_client,
        data={'email': 'user1@localhost', 'password': 'user1_password'},
    )
    assert isinstance(user_guid, uuid.UUID)

    # Cleanup
    from app.modules.users.models import User

    user1_instance = User.query.get(user_guid)
    assert user1_instance.email == 'user1@localhost'
    assert user1_instance.password == 'user1_password'

    with db.session.begin():
        db.session.delete(user1_instance)


def test_new_user_creation_without_captcha_must_fail(flask_app_client):
    # pylint: disable=invalid-name
    response = create_new_user(
        flask_app_client,
        data={
            'recaptcha_key': None,
            'email': 'user1@localhost',
            'password': 'user1_password',
        },
        must_succeed=False,
    )
    assert response.status_code == 403
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


def test_new_user_creation_with_incorrect_captcha_must_fail(flask_app_client):
    # pylint: disable=invalid-name
    response = create_new_user(
        flask_app_client,
        data={
            'recaptcha_key': 'invalid_captcha_key',
            'email': 'user1@localhost',
            'password': 'user1_password',
        },
        must_succeed=False,
    )
    assert response.status_code == 403
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}


def test_new_user_creation_without_captcha_but_admin_user(
    patch_User_password_scheme, flask_app_client, admin_user, db
):
    # pylint: disable=invalid-name,unused-argument
    with flask_app_client.login(admin_user):
        user_guid = create_new_user(
            flask_app_client,
            data={
                'recaptcha_key': None,
                'email': 'user1@localhost',
                'password': 'user1_password',
            },
        )
    assert isinstance(user_guid, uuid.UUID)

    # Cleanup
    from app.modules.users.models import User

    user1_instance = User.query.get(user_guid)
    assert user1_instance.email == 'user1@localhost'
    assert user1_instance.password == 'user1_password'

    with db.session.begin():
        db.session.delete(user1_instance)


def test_new_user_creation_duplicate_must_fail(flask_app_client, db):
    # pylint: disable=invalid-name
    user_guid = create_new_user(
        flask_app_client,
        data={'email': 'user1@localhost', 'password': 'user1_password'},
    )
    response = create_new_user(
        flask_app_client,
        data={'email': 'user1@localhost', 'password': 'user1_password'},
        must_succeed=False,
    )
    assert response.status_code == 409
    assert response.content_type == 'application/json'
    assert set(response.json.keys()) >= {'status', 'message'}

    # Cleanup
    from app.modules.users.models import User

    user1_instance = User.query.get(user_guid)
    with db.session.begin():
        db.session.delete(user1_instance)
