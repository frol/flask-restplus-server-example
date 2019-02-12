# encoding: utf-8
# pylint: disable=too-few-public-methods
"""
RESTful API User resources
--------------------------
"""

import logging

from flask_login import current_user
from flask_restplus_patched import Resource
from flask_restplus._http import HTTPStatus

from app.extensions.api import Namespace

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
    @api.response(schemas.BaseUserSchema(many=True))
    @api.paginate()
    def get(self, args):
        """
        List of users.

        Returns a list of users starting from ``offset`` limited by ``limit``
        parameter.
        """
        return User.query.offset(args['offset']).limit(args['limit'])

    @api.parameters(parameters.AddUserParameters())
    @api.response(schemas.DetailedUserSchema())
    @api.response(code=HTTPStatus.FORBIDDEN)
    @api.response(code=HTTPStatus.CONFLICT)
    @api.doc(id='create_user')
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


@api.route('/signup-form')
class UserSignupForm(Resource):
    """
    Use signup form helpers.
    """

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
@api.login_required(oauth_scopes=['users:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND,
    description="User not found.",
)
@api.resolve_object_by_model(User, 'user')
class UserByID(Resource):
    """
    Manipulations with a specific user.
    """

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
    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['user']}
    )
    @api.permission_required(permissions.WriteAccessPermission())
    @api.parameters(parameters.PatchUserDetailsParameters())
    @api.response(schemas.DetailedUserSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def patch(self, args, user):
        """
        Patch user details by ID.
        """
        with api.commit_or_abort(
                db.session,
                default_error_message="Failed to update user details."
            ):
            parameters.PatchUserDetailsParameters.perform_patch(args, user)
            db.session.merge(user)
        return user


@api.route('/me')
@api.login_required(oauth_scopes=['users:read'])
class UserMe(Resource):
    """
    Useful reference to the authenticated user itself.
    """

    @api.response(schemas.DetailedUserSchema())
    def get(self):
        """
        Get current user details.
        """
        return User.query.get_or_404(current_user.id)
