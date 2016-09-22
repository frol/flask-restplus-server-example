# encoding: utf-8
# pylint: disable=too-few-public-methods,invalid-name,bad-continuation
"""
RESTful API User resources
--------------------------
"""

import logging

from flask_login import current_user
from flask_restplus import Resource

from app.extensions.api import Namespace, abort, http_exceptions
from app.extensions.api.parameters import PaginationParameters

from . import permissions, schemas, parameters
from .models import db, User


log = logging.getLogger(__name__)
api = Namespace('users', description="Users")


@api.route('/')
class Users(Resource):
    """
    Manipulations with users.
    """

    @api.login_required(oauth_scopes=['users:read'])
    @api.permission_required(permissions.AdminRolePermission())
    @api.parameters(PaginationParameters())
    @api.response(schemas.BaseUserSchema(many=True))
    def get(self, args):
        """
        List of users.

        Returns a list of users starting from ``offset`` limited by ``limit``
        parameter.
        """
        return User.query.offset(args['offset']).limit(args['limit'])

    @api.parameters(parameters.AddUserParameters())
    @api.response(schemas.DetailedUserSchema())
    @api.response(code=http_exceptions.Forbidden.code)
    @api.response(code=http_exceptions.Conflict.code)
    def post(self, args):
        """
        Create a new user.
        """
        with api.commit_or_abort(
                db.session,
                default_error_message="Failed to create a new user."
            ):
            new_user = User(**args)
            db.session.add(new_user)
        return new_user


@api.route('/signup_form')
class UserSignupForm(Resource):

    @api.response(schemas.UserSignupFormSchema())
    def get(self):
        """
        Get signup form keys.

        This endpoint must be used in order to get a server reCAPTCHA public key which
        must be used to receive a reCAPTCHA secret key for POST /users/ form.
        """
        # TODO:
        return {"recaptcha_server_key": "TODO"}


@api.route('/<int:user_id>')
@api.response(
    code=http_exceptions.NotFound.code,
    description="User not found.",
)
class UserByID(Resource):
    """
    Manipulations with a specific user.
    """

    @api.login_required(oauth_scopes=['users:read'])
    @api.resolve_object_by_model(User, 'user')
    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['user']}
    )
    @api.response(schemas.DetailedUserSchema())
    def get(self, user):
        """
        Get user details by ID.
        """
        return user

    @api.login_required(oauth_scopes=['users:write'])
    @api.resolve_object_by_model(User, 'user')
    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['user']}
    )
    @api.permission_required(permissions.WriteAccessPermission())
    @api.parameters(parameters.PatchUserDetailsParameters())
    @api.response(schemas.DetailedUserSchema())
    @api.response(code=http_exceptions.Conflict.code)
    def patch(self, args, user):
        """
        Patch user details by ID.
        """
        state = {'current_password': None}

        with api.commit_or_abort(
                db.session,
                default_error_message="Failed to update user details."
            ):
            parameters.PatchUserDetailsParameters.perform_patch(args, user, state)
            db.session.merge(user)
        return user


@api.route('/me')
class UserMe(Resource):
    """
    Useful reference to the authenticated user itself.
    """

    @api.login_required(oauth_scopes=['users:read'])
    @api.response(schemas.DetailedUserSchema())
    def get(self):
        """
        Get current user details.
        """
        return User.query.get_or_404(current_user.id)
