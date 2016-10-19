# encoding: utf-8
# pylint: disable=invalid-name,missing-docstring

from app.modules.users import schemas


def test_BaseUserSchema_dump_empty_input():
    dumped_result = schemas.BaseUserSchema().dump({})
    assert dumped_result.errors == {}
    assert dumped_result.data == {}

def test_BaseUserSchema_dump_user_instance(user_instance):
    user_instance.password = "password"
    dumped_result = schemas.BaseUserSchema().dump(user_instance)
    assert dumped_result.errors == {}
    assert 'password' not in dumped_result.data
    assert set(dumped_result.data.keys()) == {
        'id',
        'username',
        'first_name',
        'middle_name',
        'last_name'
    }

def test_DetailedUserSchema_dump_user_instance(user_instance):
    user_instance.password = "password"
    dumped_result = schemas.DetailedUserSchema().dump(user_instance)
    assert dumped_result.errors == {}
    assert 'password' not in dumped_result.data
    assert set(dumped_result.data.keys()) == {
        'id',
        'username',
        'first_name',
        'middle_name',
        'last_name',
        'email',
        'created',
        'updated',
        'is_active',
        'is_regular_user',
        'is_admin',
    }

def test_UserSignupFormSchema_dump():
    form_data = {'recaptcha_server_key': 'key'}
    dumped_result = schemas.UserSignupFormSchema().dump(form_data)
    assert dumped_result.errors == {}
    assert dumped_result.data == form_data
