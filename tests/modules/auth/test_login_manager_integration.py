from mock import Mock, patch

from flask import request

from app.modules import auth


def test_loading_user_from_request(flask_app):
    mock_user = Mock()
    with flask_app.test_request_context('/'):
        request.oauth = Mock()
        request.oauth.user = mock_user
        assert auth.load_user_from_request(request) == mock_user
        del request.oauth
    # TODO: test oauth2.verify_request case
