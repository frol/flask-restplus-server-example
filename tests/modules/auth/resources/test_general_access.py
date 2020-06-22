# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
import pytest


@pytest.mark.parametrize(
    'http_method,http_path',
    (('GET', '/api/v1/auth/clients'), ('POST', '/api/v1/auth/clients'),),
)
def test_unauthorized_access(http_method, http_path, flask_app_client):
    response = flask_app_client.open(method=http_method, path=http_path)
    print(response)
    assert response.status_code == 401
