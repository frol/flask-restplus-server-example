# encoding: utf-8
# pylint: disable=missing-docstring
import json

from jsonschema import RefResolver
from swagger_spec_validator import validator20


def test_openapi_spec_validity(flask_app_client):
    raw_openapi_spec = flask_app_client.get('/api/v1/swagger.json').data
    deserialized_openapi_spec = json.loads(raw_openapi_spec.decode('utf-8'))
    assert isinstance(validator20.validate_spec(deserialized_openapi_spec), RefResolver)
