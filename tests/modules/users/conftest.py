# encoding: utf-8
# pylint: disable=missing-docstring
from datetime import datetime

import pytest

from flask.ext.login import current_user, login_user, logout_user

from app.modules.users import models


@pytest.fixture()
def user_instance():
    user_id = 1
    _user_instance = models.User(
        id=user_id,
        username="username",
        first_name="First Name",
        middle_name="Middle Name",
        last_name="Last Name",
        password=None,
        email="user@email.com",
        created=datetime.now(),
        updated=datetime.now(),
        is_active=True,
        is_readonly=False,
        is_admin=False,
    )
    _user_instance.get_id = lambda: user_id
    return _user_instance

@pytest.yield_fixture()
def authenticated_user_instance(flask_app):
    with flask_app.test_request_context('/'):
        login_user(user_instance())
        yield current_user
        logout_user()

@pytest.yield_fixture()
def anonymous_user_instance(flask_app):
    with flask_app.test_request_context('/'):
        yield current_user
