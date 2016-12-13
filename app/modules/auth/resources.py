# encoding: utf-8
# pylint: disable=too-few-public-methods,invalid-name,bad-continuation
"""
RESTful API Auth resources
--------------------------
"""

import logging

from flask_login import current_user
from flask_restplus_patched import Resource
from flask_restplus_patched._http import HTTPStatus
from werkzeug import security

from app.extensions.api import Namespace

from . import schemas, parameters
from .models import db, OAuth2Client


log = logging.getLogger(__name__)
api = Namespace('auth', description="Authentication")


@api.route('/oauth2_clients/')
@api.login_required(oauth_scopes=['auth:read'])
class OAuth2Clients(Resource):
    """
    Manipulations with OAuth2 clients.
    """

    @api.parameters(parameters.ListOAuth2ClientsParameters())
    @api.response(schemas.BaseOAuth2ClientSchema(many=True))
    def get(self, args):
        """
        List of OAuth2 Clients.

        Returns a list of OAuth2 Clients starting from ``offset`` limited by
        ``limit`` parameter.
        """
        oauth2_clients = OAuth2Client.query
        if 'user_id' in args:
            oauth2_clients = oauth2_clients.filter(
                OAuth2Client.user_id == args['user_id']
            )
        return oauth2_clients.offset(args['offset']).limit(args['limit'])

    @api.login_required(oauth_scopes=['auth:write'])
    @api.parameters(parameters.CreateOAuth2ClientParameters())
    @api.response(schemas.DetailedOAuth2ClientSchema())
    @api.response(code=HTTPStatus.FORBIDDEN)
    @api.response(code=HTTPStatus.CONFLICT)
    @api.doc(id='create_oauth_client')
    def post(self, args):
        """
        Create a new OAuth2 Client.

        Essentially, OAuth2 Client is a ``client_id`` and ``client_secret``
        pair associated with a user.
        """
        with api.commit_or_abort(
                db.session,
                default_error_message="Failed to create a new OAuth2 client."
            ):
            # TODO: reconsider using gen_salt
            new_oauth2_client = OAuth2Client(
                user_id=current_user.id,
                client_id=security.gen_salt(40),
                client_secret=security.gen_salt(50),
                **args
            )
            db.session.add(new_oauth2_client)
        return new_oauth2_client
