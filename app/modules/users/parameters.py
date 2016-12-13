# encoding: utf-8
# pylint: disable=wrong-import-order
"""
Input arguments (Parameters) for User resources RESTful API
-----------------------------------------------------------
"""

from flask_login import current_user
from flask_marshmallow import base_fields
from flask_restplus_patched import PostFormParameters, PatchJSONParameters
from flask_restplus_patched._http import HTTPStatus
from marshmallow import validates_schema, ValidationError

from app.extensions.api import abort

from . import schemas, permissions
from .models import User


class AddUserParameters(PostFormParameters, schemas.BaseUserSchema):
    """
    New user creation (sign up) parameters.
    """

    username = base_fields.String(description="Example: root", required=True)
    email = base_fields.Email(description="Example: root@gmail.com", required=True)
    password = base_fields.String(description="No rules yet", required=True)
    recaptcha_key = base_fields.String(
        description=(
            "See `/users/signup_form` for details. It is required for everybody, except admins"
        ),
        required=False
    )

    class Meta(schemas.BaseUserSchema.Meta):
        fields = schemas.BaseUserSchema.Meta.fields + (
            'email',
            'password',
            'recaptcha_key',
        )

    @validates_schema
    def validate_captcha(self, data):
        """"
        Check reCAPTCHA if necessary.

        NOTE: we remove 'recaptcha_key' from data once checked because we don't need it
        in the resource
        """
        recaptcha_key = data.pop('recaptcha_key', None)
        captcha_is_valid = False
        if not recaptcha_key:
            no_captcha_permission = permissions.AdminRolePermission()
            if no_captcha_permission.check():
                captcha_is_valid = True
        # NOTE: This hardcoded CAPTCHA key is just for demo purposes.
        elif recaptcha_key == 'secret_key':
            captcha_is_valid = True

        if not captcha_is_valid:
            abort(code=HTTPStatus.FORBIDDEN, message="CAPTCHA key is incorrect.")


class PatchUserDetailsParameters(PatchJSONParameters):
    # pylint: disable=abstract-method
    """
    User details updating parameters following PATCH JSON RFC.
    """

    PATH_CHOICES = tuple(
        '/%s' % field for field in (
            'current_password',
            User.first_name.key,
            User.middle_name.key,
            User.last_name.key,
            User.password.key,
            User.email.key,
            User.is_active.fget.__name__,
            User.is_regular_user.fget.__name__,
            User.is_admin.fget.__name__,
        )
    )

    @classmethod
    def test(cls, obj, field, value, state):
        """
        Additional check for 'current_password' as User hasn't field 'current_password'
        """
        if field == 'current_password':
            if current_user.password != value and obj.password != value:
                abort(code=HTTPStatus.FORBIDDEN, message="Wrong password")
            else:
                state['current_password'] = value
                return True
        return PatchJSONParameters.test(obj, field, value, state)

    @classmethod
    def replace(cls, obj, field, value, state):
        """
        Some fields require extra permissions to be changed.

        Changing `is_active` and `is_regular_user` properties, current user
        must be a supervisor of the changing user, and `current_password` of
        the current user should be provided.

        Changing `is_admin` property requires current user to be Admin, and
        `current_password` of the current user should be provided..
        """
        if 'current_password' not in state:
            raise ValidationError(
                "Updating sensitive user settings requires `current_password` test operation "
                "performed before replacements."
            )

        if field in {User.is_active.fget.__name__, User.is_regular_user.fget.__name__}:
            with permissions.SupervisorRolePermission(
                    obj=obj,
                    password_required=True,
                    password=state['current_password']
                ):
                # Access granted
                pass
        elif field == User.is_admin.fget.__name__:
            with permissions.AdminRolePermission(
                    password_required=True,
                    password=state['current_password']
                ):
                # Access granted
                pass
        return super(PatchUserDetailsParameters, cls).replace(obj, field, value, state)
