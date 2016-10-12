# encoding: utf-8
# pylint: disable=missing-docstring
import pytest

from app import create_app


@pytest.mark.parametrize('flask_config_name', ['production', 'development'])
def test_create_app(flask_config_name):
    create_app(flask_config_name=flask_config_name)
