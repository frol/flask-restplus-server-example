# encoding: utf-8
# pylint: disable=missing-docstring,redefined-outer-name
import pytest

from flask_login import current_user, login_user, logout_user

from tests import utils

from app.modules.users import models


@pytest.yield_fixture()
def patch_User_password_scheme():
    # pylint: disable=invalid-name,protected-access
    """
    By default, the application uses ``bcrypt`` to store passwords securely.
    However, ``bcrypt`` is a slow hashing algorithm (by design), so it is
    better to downgrade it to ``plaintext`` while testing, since it will save
    us quite some time.
    """
    # NOTE: It seems a hacky way, but monkeypatching is a hack anyway.
    password_field_context = models.User.password.property.columns[0].type.context
    # NOTE: This is used here to forcefully resolve the LazyCryptContext
    password_field_context.context_kwds
    password_field_context._config._init_scheme_list(('plaintext', ))
    password_field_context._config._init_records()
    password_field_context._config._init_default_schemes()
    yield
    password_field_context._config._init_scheme_list(('bcrypt', ))
    password_field_context._config._init_records()
    password_field_context._config._init_default_schemes()

@pytest.fixture()
def user_instance(patch_User_password_scheme):
    # pylint: disable=unused-argument,invalid-name
    user_id = 1
    _user_instance = utils.generate_user_instance(user_id=user_id)
    _user_instance.get_id = lambda: user_id
    return _user_instance

@pytest.yield_fixture()
def authenticated_user_instance(flask_app, user_instance):
    with flask_app.test_request_context('/'):
        login_user(user_instance)
        yield current_user
        logout_user()

@pytest.yield_fixture()
def anonymous_user_instance(flask_app):
    with flask_app.test_request_context('/'):
        yield current_user
