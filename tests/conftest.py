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
def flask_app_client(flask_app):
    flask_app.test_client_class = utils.AutoAuthFlaskClient
    flask_app.response_class = utils.JSONResponse
    return flask_app.test_client()


@pytest.yield_fixture(scope='session')
def regular_user(db):
    regular_user_instance = utils.generate_user_instance(
        username='regular_user'
    )

    with db.session.begin():
        db.session.add(regular_user_instance)

    yield regular_user_instance

    with db.session.begin():
        db.session.delete(regular_user_instance)


@pytest.yield_fixture(scope='session')
def readonly_user(db):
    readonly_user_instance = utils.generate_user_instance(
        username='readonly_user',
        is_regular_user=False
    )

    with db.session.begin():
        db.session.add(readonly_user_instance)

    yield readonly_user_instance

    with db.session.begin():
        db.session.delete(readonly_user_instance)


@pytest.yield_fixture(scope='session')
def admin_user(db):
    admin_user_instance = utils.generate_user_instance(
        username='admin_user',
        is_admin=True
    )

    with db.session.begin():
        db.session.add(admin_user_instance)

    yield admin_user_instance

    with db.session.begin():
        db.session.delete(admin_user_instance)


@pytest.yield_fixture(scope='session')
def internal_user(db):
    internal_user_instance = utils.generate_user_instance(
        username='internal_user',
        is_regular_user=False,
        is_admin=False,
        is_active=True,
        is_internal=True
    )

    with db.session.begin():
        db.session.add(internal_user_instance)

    yield internal_user_instance

    with db.session.begin():
        db.session.delete(internal_user_instance)
