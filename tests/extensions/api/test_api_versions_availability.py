import pytest

from app.extensions import api


@pytest.mark.parametrize('api_version', [
        '1',
    ])
def test_extension_availability(api_version):
    assert hasattr(api, 'api_v%s' % api_version)
