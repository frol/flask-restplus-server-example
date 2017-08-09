from datetime import datetime, timedelta

from mock import Mock

from flask import request

from app.modules import auth


def test_loading_user_from_anonymous_request(flask_app):
    with flask_app.test_request_context('/'):
        assert auth.load_user_from_request(request) is None

def test_loading_user_from_request_with_oauth_user_cached(flask_app):
    mock_user = Mock()
    with flask_app.test_request_context('/'):
        request.oauth = Mock()
        request.oauth.user = mock_user
        assert auth.load_user_from_request(request) == mock_user
        del request.oauth

def test_loading_user_from_request_with_bearer_token(flask_app, db, regular_user_oauth2_client):
    oauth2_bearer_token = auth.models.OAuth2Token(
        client=regular_user_oauth2_client,
        user=regular_user_oauth2_client.user,
        token_type='Bearer',
        access_token='test_access_token',
        scopes=[],
        expires=datetime.utcnow() + timedelta(days=1),
    )

    with db.session.begin():
        db.session.add(oauth2_bearer_token)

    with flask_app.test_request_context(
        path='/',
        headers=(
            ('Authorization', 'Bearer %s' % oauth2_bearer_token.access_token),
        )
    ):
        assert auth.load_user_from_request(request) == regular_user_oauth2_client.user

    with db.session.begin():
        db.session.delete(oauth2_bearer_token)
