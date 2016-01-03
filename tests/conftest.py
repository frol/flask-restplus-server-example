# encoding: utf-8
# pylint: disable=redefined-outer-name,too-many-ancestors,missing-docstring
import json
import pytest

from flask import Response
from werkzeug.utils import cached_property

from app import create_app


@pytest.yield_fixture(scope='session')
def flask_app():
    from config import TestingConfig
    TestingConfig.init()

    app = create_app(flask_config='testing')
    from app.extensions import db

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

    TestingConfig.destroy()


class JSONResponse(Response):

    @cached_property
    def json(self):
        return json.loads(self.get_data(as_text=True))


@pytest.yield_fixture(scope='session')
def flask_app_client(flask_app):
    flask_app.response_class = JSONResponse
    yield flask_app.test_client()
