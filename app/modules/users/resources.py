# encoding: utf-8
"""
Users API resources
"""
import logging

from flask.ext.login import current_user
from flask.ext.restplus import Resource
from flask_restplus_patched import DefaultHTTPErrorSchema
from werkzeug import exceptions as http_exceptions

from app.extensions import api
from app.modules.auth.decorators import login_required

from . import permissions, schemas, parameters
from .models import db, User


log = logging.getLogger(__name__)
namespace = api.api_v1.namespace('users', description="Users")


@namespace.route('/')
class Users(Resource):
    """
    Manipulations with users.
    """

    @login_required(api.api_v1, scopes=['users:read'])
    @permissions.AdminRolePermission(api.api_v1)
    @parameters.PaginationParameters(api.api_v1)
    @schemas.BaseUserSchema(api.api_v1, many=True)
    def get(self, args):
        """
        List of users.

        Returns a list of users starting from ``offset`` limited by ``limit``
        parameter.
        """
        return User.query.all()[args['offset']: args['offset'] + args['limit']]

    @parameters.AddUserParameters(api.api_v1)
    @schemas.DetailedUserSchema(api.api_v1)
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
            api.abort(code=http_exceptions.Forbidden.code, message="CAPTCHA key is incorrect.")
        
        new_user = User.create(**args)
        # TODO: handle errors better
        if new_user is None:
            api.abort(code=http_exceptions.Conflict.code, message="Could not create a new user.")
        
        return new_user


@namespace.route('/signup_form')
class UserSignupForm(Resource):

    @schemas.UserSignupFormSchema(api.api_v1)
    def get(self):
        """
        Get signup form keys.

        This endpoint must be used in order to get a server reCAPTCHA public key which
        must be used to receive a reCAPTCHA secret key for POST /users/ form.
        """
        # TODO:
        return {"recaptcha_server_key": "TODO"}


@namespace.route('/<int:user_id>')
@DefaultHTTPErrorSchema(api.api_v1, code=http_exceptions.NotFound.code, description="User not found")
class UserByID(Resource):
    """
    Manipulations with a specific user.
    """

    @login_required(api.api_v1, scopes=['users:read'])
    @permissions.AdminRolePermission(api.api_v1)
    @schemas.DetailedUserSchema(api.api_v1)
    def get(self, user_id):
        """
        Get user details by ID.
        """
        return User.query.get_or_404(user_id)

    @login_required(api.api_v1, scopes=['users:write'])
    @parameters.PatchUserDetailsParameters(api.api_v1)
    @schemas.DetailedUserSchema(api.api_v1)
    def patch(self, args, user_id):
        """
        Patch user details by ID.
        """
        user = User.query.get_or_404(user_id)
        
        with permissions.OwnerRolePermission(obj=user):
            with permissions.WriteAccessPermission():
                state = {'current_password': None}

                for operation in args['body']:
                    if not self._process_patch_operation(operation, user=user, state=state): 
                        log.info("User patching has ignored unknown operation %s", operation)
                                    
                db.session.merge(user)
                db.session.commit()
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
            api.abort(code=http_exceptions.UnprocessableEntity.code, message="value is required")

        if operation['op'] == parameters.PatchUserDetailsParameters.OP_TEST:
            if operation['path'] == '/current_password':
                state['current_password'] = operation['value']
                if (
                    not current_user.verify_password(state['current_password'])
                    and
                    not user.verify_password(state['current_password'])
                ):
                    api.abort(code=http_exceptions.Forbidden.code, message="Wrong password")
                return True
        
        elif operation['op'] == parameters.PatchUserDetailsParameters.OP_REPLACE:
            assert operation['path'][0] == '/', "Path must always begin with /"
            field_name = operation['path'][1:]
            field_value = operation['value']
            
            if field_name in ('is_active', 'is_readonly', 'is_admin'):
                
                if field_name == 'is_admin':
                    with permissions.AdminRolePermission(
                            password_required=True,
                            password=state['current_password']
                    ):
                        static_role = user.SR_ADMIN
                
                elif field_name == 'is_active':
                    with permissions.SupervisorRolePermission(
                            obj=user,
                            password_required=True,
                            password=state['current_password']
                    ):
                        static_role = user.SR_ACTIVE
                
                elif field_name == 'is_readonly':
                    with permissions.SupervisorRolePermission(
                            obj=user,
                            password_required=True,
                            password=state['current_password']
                    ):
                        static_role = user.SR_READONLY
                
                if field_value:
                    user.set_static_role(static_role, commit=False)
                
                else:
                    user.unset_static_role(static_role, commit=False)
            
            elif field_name == 'password':
                user.set_password(field_value, commit=False)
            
            else:
                setattr(user, field_name, field_value)
            return True
        return False


@namespace.route('/me')
class UserMe(Resource):
    """
    Useful reference to the authenticated user itself.
    """

    @login_required(api.api_v1, scopes=['users:read'])
    @schemas.DetailedUserSchema(api.api_v1)
    def get(self):
        """
        Get current user details.
        """
        return User.query.get_or_404(current_user.id)
