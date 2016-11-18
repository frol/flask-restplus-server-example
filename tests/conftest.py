# encoding: utf-8
# pylint: disable=redefined-outer-name,missing-docstring
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

@pytest.yield_fixture()
def db(flask_app):
    # pylint: disable=unused-argument,invalid-name
    from app.extensions import db as db_instance
    yield db_instance
    db_instance.session.rollback()

@pytest.fixture(scope='session')
def flask_app_client(flask_app):
    flask_app.test_client_class = utils.AutoAuthFlaskClient
    flask_app.response_class = utils.JSONResponse
    return flask_app.test_client()

@pytest.yield_fixture(scope='session')
def regular_user(flask_app):
    # pylint: disable=invalid-name,unused-argument
    from app.extensions import db

    regular_user_instance = utils.generate_user_instance(
        username='regular_user'
    )

    db.session.add(regular_user_instance)
    db.session.commit()
    yield regular_user_instance
    db.session.delete(regular_user_instance)
    db.session.commit()

@pytest.yield_fixture(scope='session')
def readonly_user(flask_app):
    # pylint: disable=invalid-name,unused-argument
    from app.extensions import db

    readonly_user_instance = utils.generate_user_instance(
        username='readonly_user',
        is_regular_user=False
    )

    db.session.add(readonly_user_instance)
    db.session.commit()
    yield readonly_user_instance
    db.session.delete(readonly_user_instance)
    db.session.commit()

@pytest.yield_fixture(scope='session')
def admin_user(flask_app):
    # pylint: disable=invalid-name,unused-argument
    from app.extensions import db

    admin_user_instance = utils.generate_user_instance(
        username='admin_user',
        is_admin=True
    )

    db.session.add(admin_user_instance)
    db.session.commit()
    yield admin_user_instance
    db.session.delete(admin_user_instance)
    db.session.commit()

@pytest.yield_fixture(scope='session')
def internal_user(flask_app):
    # pylint: disable=invalid-name,unused-argument
    from app.extensions import db

    internal_user_instance = utils.generate_user_instance(
        username='internal_user',
        is_regular_user=False,
        is_admin=False,
        is_active=True,
        is_internal=True
    )

    db.session.add(internal_user_instance)
    db.session.commit()
    yield internal_user_instance
    db.session.delete(internal_user_instance)
    db.session.commit()
