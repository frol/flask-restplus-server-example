# encoding: utf-8
# pylint: disable=missing-docstring
import pytest

from app import create_app


@pytest.mark.parametrize('flask_config', ['production', 'development'])
def test_create_app(flask_config):
    create_app(flask_config=flask_config)
