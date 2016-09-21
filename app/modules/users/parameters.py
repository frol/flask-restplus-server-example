# encoding: utf-8
"""
Input arguments (Parameters) for User resources RESTful API
-----------------------------------------------------------
"""

from flask_marshmallow import base_fields
from marshmallow import validates_schema

from app.extensions.api import abort, http_exceptions
from flask_restplus_patched import PostFormParameters, PatchJSONParameters

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
        elif recaptcha_key == 'secret_key':
            captcha_is_valid = True

        if not captcha_is_valid:
            abort(code=http_exceptions.Forbidden.code, message="CAPTCHA key is incorrect.")


class PatchUserDetailsParameters(PatchJSONParameters):
    PATH_CHOICES = tuple(
        '/%s' % field for field in (
            'current_password',
            User.first_name.key,
            User.middle_name.key,
            User.last_name.key,
            User.password.key,
            User.email.key,
            User.is_active.fget.__name__,
            User.is_readonly.fget.__name__,
            User.is_admin.fget.__name__,
        )
    )
