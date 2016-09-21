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
            for operation in args:
                try:
                    if not self._process_patch_operation(operation, user=user, state=state):
                        log.info("User patching has ignored unknown operation %s", operation)
                except ValueError as exception:
                    abort(code=http_exceptions.Conflict.code, message=str(exception))

            db.session.merge(user)
        return user

    def _process_patch_operation(self, operation, user, state):
        """
        Args:
            operation (dict) - one patch operation in RFC 6902 format
            user (User) - user instance which is needed to be patched
            state (dict) - inter-operations state storage

        Returns:
            processing_status (bool) - True if operation was handled, otherwise False.
        """
        if 'value' not in operation:
            # TODO: handle errors better
            abort(code=http_exceptions.UnprocessableEntity.code, message="value is required")

        if operation['op'] == parameters.PatchUserDetailsParameters.OP_TEST:
            # User has to provide the admin/supervisor password (if the current
            # user has an admin or a supervisor role) or the current password
            # of the user that is edited.
            if operation['path'] == '/current_password':
                current_password = operation['value']

                if current_user.password != current_password and user.password != current_password:
                    abort(code=http_exceptions.Forbidden.code, message="Wrong password")

                state['current_password'] = current_password
                return True

        elif operation['op'] == parameters.PatchUserDetailsParameters.OP_REPLACE:
            assert operation['path'][0] == '/', "Path must always begin with /"
            field_name = operation['path'][1:]
            field_value = operation['value']

            # Some fields require extra permissions to be changed.
            # Current user has to have at least a Supervisor role to change
            # 'is_active' and 'is_readonly' property
            if field_name in {'is_active', 'is_readonly'}:
                with permissions.SupervisorRolePermission(
                    obj=user,
                    password_required=True,
                    password=state['current_password']
                ):
                    # Access granted
                    pass

            # Current user has to have an Admin role to change 'is_admin' property
            elif field_name == 'is_admin':
                with permissions.AdminRolePermission(
                    password_required=True,
                    password=state['current_password']
                ):
                    # Access granted
                    pass

            setattr(user, field_name, field_value)
            return True
        return False


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
