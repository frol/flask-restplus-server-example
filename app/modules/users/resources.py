# encoding: utf-8
# pylint: disable=too-few-public-methods,invalid-name
"""
RESTful API User resources
--------------------------
"""

import logging

from flask_login import current_user
from flask_restplus import Resource
import sqlalchemy

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
        # Check reCAPTCHA if necessary
        recaptcha_key = args.pop('recaptcha_key', None)
        captcha_is_valid = False
        if not recaptcha_key:
            no_captcha_permission = permissions.AdminRolePermission()
            if no_captcha_permission.check():
                captcha_is_valid = True
        elif recaptcha_key == 'secret_key':
            captcha_is_valid = True

        if not captcha_is_valid:
            abort(code=http_exceptions.Forbidden.code, message="CAPTCHA key is incorrect.")

        new_user = User(**args)

        db.session.add(new_user)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            # TODO: handle errors better
            abort(code=http_exceptions.Conflict.code, message="Could not create a new user.")

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
    @api.permission_required(permissions.OwnerRolePermission(partial=True))
    @api.response(schemas.DetailedUserSchema())
    def get(self, user_id):
        """
        Get user details by ID.
        """
        user = User.query.get(user_id)
        with permissions.OwnerRolePermission(obj=user):
            return user

    @api.login_required(oauth_scopes=['users:write'])
    @api.permission_required(permissions.OwnerRolePermission(partial=True))
    @api.parameters(parameters.PatchUserDetailsParameters())
    @api.response(schemas.DetailedUserSchema())
    @api.response(code=http_exceptions.Conflict.code)
    def patch(self, args, user_id):
        """
        Patch user details by ID.
        """
        user = User.query.get_or_404(user_id)

        with permissions.OwnerRolePermission(obj=user):
            with permissions.WriteAccessPermission():
                state = {'current_password': None}

                for operation in args:
                    if not self._process_patch_operation(operation, user=user, state=state):
                        log.info("User patching has ignored unknown operation %s", operation)

                try:
                    db.session.merge(user)
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError:
                    db.session.rollback()
                    # TODO: handle errors better
                    abort(
                        code=http_exceptions.Conflict.code,
                        message="Could not update user details."
                    )
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
