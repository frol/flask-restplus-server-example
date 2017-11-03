# encoding: utf-8
import pytest

from tests import utils

from app import create_app


@pytest.yield_fixture(scope='session')
def flask_app():
    app = create_app(flask_config_name='testing')
    from app.extensions import db

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.yield_fixture(scope='session')
def db(flask_app):
    from app.extensions import db as db_instance
    yield db_instance


@pytest.fixture(scope='session')
def temp_db_instance_helper(db):
    def temp_db_instance_manager(instance):
        with db.session.begin():
            db.session.add(instance)

        yield instance

        mapper = instance.__class__.__mapper__
        assert len(mapper.primary_key) == 1
        instance.__class__.query\
            .filter(mapper.primary_key[0] == mapper.primary_key_from_instance(instance)[0])\
            .delete()

    return temp_db_instance_manager


@pytest.fixture(scope='session')
def flask_app_client(flask_app):
    flask_app.test_client_class = utils.AutoAuthFlaskClient
    flask_app.response_class = utils.JSONResponse
    return flask_app.test_client()


@pytest.yield_fixture(scope='session')
def regular_user(temp_db_instance_helper):
    for _ in temp_db_instance_helper(
            utils.generate_user_instance(username='regular_user')
        ):
        yield _


@pytest.yield_fixture(scope='session')
def readonly_user(temp_db_instance_helper):
    for _ in temp_db_instance_helper(
            utils.generate_user_instance(username='readonly_user', is_regular_user=False)
        ):
        yield _


@pytest.yield_fixture(scope='session')
def admin_user(temp_db_instance_helper):
    for _ in temp_db_instance_helper(
            utils.generate_user_instance(username='admin_user', is_admin=True)
        ):
        yield _


@pytest.yield_fixture(scope='session')
def internal_user(temp_db_instance_helper):
    for _ in temp_db_instance_helper(
            utils.generate_user_instance(
                username='internal_user',
                is_regular_user=False,
                is_admin=False,
                is_active=True,
                is_internal=True
            )
        ):
        yield _
