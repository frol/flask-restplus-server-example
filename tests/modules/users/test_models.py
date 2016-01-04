# encoding: utf-8
# pylint: disable=invalid-name,missing-docstring

import pytest

from app.modules.users import models


def test_User_repr(user_instance):
    assert len(str(user_instance)) > 0

def test_User_auth(user_instance):
    assert user_instance.is_authenticated
    assert not user_instance.is_anonymous

@pytest.mark.parametrize('init_static_roles,is_active,is_readonly,is_admin', [
    (_init_static_roles, _is_active, _is_readonly, _is_admin) \
        for _init_static_roles in (
            0,
            models.User.SR_ACTIVATED | models.User.SR_READONLY | models.User.SR_ADMIN
        ) \
        for _is_active in (False, True) \
        for _is_readonly in (False, True) \
        for _is_admin in (False, True)
])
def test_User_static_roles_setting(
        init_static_roles,
        is_active,
        is_readonly,
        is_admin,
        user_instance
):
    """
    Static User Roles are saved as a bit flags into one ``static_roles``
    integer field. Ideally, it would be better implemented as a custom field,
    and the plugin would be tested separately, but for now this implementation
    is fine, so we test it as it is.
    """
    user_instance.static_roles = init_static_roles
    if is_active:
        user_instance.set_static_role(user_instance.SR_ACTIVATED)
    else:
        user_instance.unset_static_role(user_instance.SR_ACTIVATED)

    if is_readonly:
        user_instance.set_static_role(user_instance.SR_READONLY)
    else:
        user_instance.unset_static_role(user_instance.SR_READONLY)

    if is_admin:
        user_instance.set_static_role(user_instance.SR_ADMIN)
    else:
        user_instance.unset_static_role(user_instance.SR_ADMIN)

    assert user_instance.has_static_role(user_instance.SR_ACTIVATED) is is_active
    assert user_instance.has_static_role(user_instance.SR_READONLY) is is_readonly
    assert user_instance.has_static_role(user_instance.SR_ADMIN) is is_admin
    assert user_instance.is_active is is_active
    assert user_instance.is_readonly is is_readonly
    assert user_instance.is_admin is is_admin

    if not is_active and not is_readonly and not is_admin:
        assert user_instance.static_roles == 0

def test_User_check_owner(user_instance):
    assert user_instance.check_owner(user_instance)
    assert not user_instance.check_owner(models.User())

def test_User_find_with_password(db): # pylint: disable=unused-argument

    def create_user(username, password):
        user = models.User(
            username=username,
            password=password,
            first_name="any",
            middle_name="any",
            last_name="any",
            email="%s@email.com" % username,
        )
        return user

    user1 = create_user("user1", "user1password")
    user2 = create_user("user2", "user2password")
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()

    assert models.User.find_with_password("user1", "user1password") == user1
    assert models.User.find_with_password("user1", "wrong-user1password") is None
    assert models.User.find_with_password("user2", "user1password") is None
    assert models.User.find_with_password("user2", "user2password") == user2
    assert models.User.find_with_password("nouser", "userpassword") is None

    db.session.delete(user1)
    db.session.delete(user2)
    db.session.commit()
