# encoding: utf-8
"""
Users API resources
"""
import logging

from flask.ext.login import current_user
from flask.ext.restplus import Resource
from flask_restplus_patched import DefaultHTTPErrorSchema
import sqlalchemy

from app.extensions.api import api_v1, abort, http_exceptions
from app.extensions.api.parameters import PaginationParameters

from . import permissions, schemas, parameters
from .models import db, User


log = logging.getLogger(__name__)
namespace = api_v1.namespace('users', description="Users")


@namespace.route('/')
class Users(Resource):
    """
    Manipulations with users.
    """

    @api_v1.login_required(scopes=['users:read'])
    @api_v1.permission_required(permissions.AdminRolePermission())
    @api_v1.parameters(PaginationParameters())
    @api_v1.response(schemas.BaseUserSchema(many=True))
    def get(self, args):
        """
        List of users.

        Returns a list of users starting from ``offset`` limited by ``limit``
        parameter.
        """
        return User.query.all()[args['offset']: args['offset'] + args['limit']]

    @api_v1.parameters(parameters.AddUserParameters())
    @api_v1.response(schemas.DetailedUserSchema())
    @api_v1.response(code=http_exceptions.Forbidden.code)
    @api_v1.response(code=http_exceptions.Conflict.code)
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
        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            # TODO: handle errors better
            abort(code=http_exceptions.Conflict.code, message="Could not create a new user.")
        
        return new_user


@namespace.route('/signup_form')
class UserSignupForm(Resource):

    @api_v1.response(schemas.UserSignupFormSchema())
    def get(self):
        """
        Get signup form keys.

        This endpoint must be used in order to get a server reCAPTCHA public key which
        must be used to receive a reCAPTCHA secret key for POST /users/ form.
        """
        # TODO:
        return {"recaptcha_server_key": "TODO"}


@namespace.route('/<int:user_id>')
@api_v1.response(
    code=http_exceptions.NotFound.code,
    description="User not found.",
)
class UserByID(Resource):
    """
    Manipulations with a specific user.
    """

    @api_v1.login_required(scopes=['users:read'])
    @api_v1.permission_required(permissions.AdminRolePermission())
    @api_v1.response(schemas.DetailedUserSchema())
    def get(self, user_id):
        """
        Get user details by ID.
        """
        return User.query.get_or_404(user_id)

    @api_v1.login_required(scopes=['users:write'])
    @api_v1.parameters(parameters.PatchUserDetailsParameters())
    @api_v1.response(schemas.DetailedUserSchema())
    @api_v1.response(code=http_exceptions.UnprocessableEntity.code)
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
            abort(code=http_exceptions.UnprocessableEntity.code, message="value is required")

        if operation['op'] == parameters.PatchUserDetailsParameters.OP_TEST:
            if operation['path'] == '/current_password':
                state['current_password'] = operation['value']
                if (
                    not current_user.password == state['current_password']
                    and
                    not user.password == state['current_password']
                ):
                    abort(code=http_exceptions.Forbidden.code, message="Wrong password")
                return True
        
        elif operation['op'] == parameters.PatchUserDetailsParameters.OP_REPLACE:
            assert operation['path'][0] == '/', "Path must always begin with /"
            field_name = operation['path'][1:]
            field_value = operation['value']
            
            if field_name in {'is_active', 'is_readonly'}:
                with permissions.SupervisorRolePermission(
                    obj=user,
                    password_required=True,
                    password=state['current_password']
                ):
                    pass
            elif field_name == 'is_admin':
                with permissions.AdminRolePermission(
                    password_required=True,
                    password=state['current_password']
                ):
                    pass

            setattr(user, field_name, field_value)
            return True
        return False


@namespace.route('/me')
class UserMe(Resource):
    """
    Useful reference to the authenticated user itself.
    """

    @api_v1.login_required(scopes=['users:read'])
    @api_v1.response(schemas.DetailedUserSchema())
    def get(self):
        """
        Get current user details.
        """
        return User.query.get_or_404(current_user.id)
