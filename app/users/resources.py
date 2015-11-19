# encoding: utf-8
"""
Users API resources
"""
import logging
import six

from flask.ext.login import current_user
from flask.ext.restplus import Resource
from flask_restplus_patched import abort
from webargs import fields
from webargs.flaskparser import use_args

from app import api, DefaultHTTPErrorSchema
from app.auth.decorators import login_required

from . import permissions, schemas, parameters
from .models import db, User


log = logging.getLogger(__name__)
namespace = api.namespace('users', description="Users")


@namespace.route('/')
class Users(Resource):
    """
    Manipulations with users.
    """

    @login_required(api, scopes=['users:read'])
    @permissions.AdminRolePermission(api)
    @parameters.PaginationParameters(api)
    @schemas.BaseUserSchema(api, many=True)
    def get(self, args):
        """
        List of users.

        Returns a list of users starting from ``offset`` limited by ``limit``
        parameter.
        """
        return User.query.all()[args['offset']: args['offset'] + args['limit']]

    @parameters.AddUserParameters(api)
    @schemas.DetailedUserSchema(api)
    def post(self, args):
        """
        Create a new user.
        """
        # Check reCAPTCHA if necessary
        recaptcha_key = args.pop('recaptcha_key', None)
        if recaptcha_key is None:
            with permissions.AdminRolePermission():
                pass
        elif recaptcha_key != 'secret_key':
            abort(code=403, message="CAPTCHA key is incorrect")
        
        new_user = User.create(**args)
        # TODO: handle errors better
        if new_user is None:
            abort(code=409, message="Could not create a new user.")
        
        return new_user


@namespace.route('/signup_form')
class UserSignupForm(Resource):

    @schemas.UserSignupFormSchema(api)
    def get(self):
        """
        Get signup form keys.

        This endpoint must be used in order to get a server reCAPTCHA public key which
        must be used to receive a reCAPTCHA secret key for POST /users/ form.
        """
        # TODO:
        return {"recaptcha_server_key": "TODO"}


@namespace.route('/<int:user_id>')
@DefaultHTTPErrorSchema(api, code=404, description="User not found")
class UserByID(Resource):
    """
    Manipulations with a specific user.
    """

    @login_required(api, scopes=['users:read'])
    @permissions.AdminRolePermission(api)
    @schemas.DetailedUserSchema(api)
    def get(self, user_id):
        """
        Get user details by ID.
        """
        return User.query.get_or_404(user_id)

    @login_required(api, scopes=['users:write'])
    @parameters.PatchUserDetailsParameters(api)
    @schemas.DetailedUserSchema(api)
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
            abort(code=422, message="value is required")

        if operation['op'] == parameters.PatchUserDetailsParameters.OP_TEST:
            if operation['path'] == '/current_password':
                state['current_password'] = operation['value']
                if (
                    not current_user.verify_password(state['current_password'])
                    and
                    not user.verify_password(state['current_password'])
                ):
                    abort(code=403, message="Wrong password")
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

    @login_required(api, scopes=['users:read'])
    @schemas.DetailedUserSchema(api)
    def get(self):
        """
        Get current user details.
        """
        return User.query.get_or_404(current_user.id)
