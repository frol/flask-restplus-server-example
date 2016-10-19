# encoding: utf-8
# pylint: disable=missing-docstring
"""
This file contains initialization data for development usage only.

You can execute this code via ``invoke app.db.init_development_data``
"""
from app.extensions import db, api

from app.modules.users.models import User
from app.modules.auth.models import OAuth2Client


def init_users():
    root_user = User(
        username='root',
        email='root@localhost',
        password='q',
        is_active=True,
        is_regular_user=True,
        is_admin=True
    )
    db.session.add(root_user)
    docs_user = User(
        username='documentation',
        email='documentation@localhost',
        password='w',
        is_active=False
    )
    db.session.add(docs_user)
    regular_user = User(
        username='user',
        email='user@localhost',
        password='w',
        is_active=True,
        is_regular_user=True
    )
    db.session.add(regular_user)
    db.session.commit()
    return root_user, docs_user, regular_user

def init_auth(docs_user):
    # TODO: OpenAPI documentation has to have OAuth2 Implicit Flow instead
    # of Resource Owner Password Credentials Flow
    oauth2_client = OAuth2Client(
        client_id='documentation',
        client_secret='KQ()SWK)SQK)QWSKQW(SKQ)S(QWSQW(SJ*HQ&HQW*SQ*^SSQWSGQSG',
        user_id=docs_user.id,
        _default_scopes=' '.join(api.api_v1.authorizations['oauth2_password']['scopes'])
    )
    db.session.add(oauth2_client)
    db.session.commit()
    return oauth2_client

def init():
    # pylint: disable=unused-variable
    assert User.query.count() == 0, \
        "Database is not empty. You should not re-apply fixtures! Aborted."

    root_user, docs_user, regular_user = init_users()
    init_auth(docs_user)
