# pylint: disable=missing-docstring

from datetime import datetime, timedelta

from mock import Mock

from flask import request

from app.modules import auth


def test_loading_user_from_anonymous_request(flask_app):
    # pylint: disable=invalid-name
    with flask_app.test_request_context('/'):
        assert auth.load_user_from_request(request) is None

def test_loading_user_from_request_with_oauth_user_cached(flask_app):
    # pylint: disable=invalid-name
    mock_user = Mock()
    with flask_app.test_request_context('/'):
        request.oauth = Mock()
        request.oauth.user = mock_user
        assert auth.load_user_from_request(request) == mock_user
        del request.oauth

def test_loading_user_from_request_with_bearer_token(flask_app, db, regular_user):
    # pylint: disable=invalid-name
    oauth2_bearer_token = auth.models.OAuth2Token(
        client_id=0,
        user=regular_user,
        token_type='Bearer',
        access_token='test_access_token',
        scopes=[],
        expires=datetime.utcnow() + timedelta(days=1),
    )

    db.session.add(oauth2_bearer_token)
    db.session.commit()

    with flask_app.test_request_context(
        path='/',
        headers=(
            ('Authorization', 'Bearer %s' % oauth2_bearer_token.access_token),
        )
    ):
        assert auth.load_user_from_request(request) == regular_user

    db.session.delete(oauth2_bearer_token)
    db.session.commit()
