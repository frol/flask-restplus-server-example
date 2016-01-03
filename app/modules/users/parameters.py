# encoding: utf-8
"""
Input arguments (Parameters) for User resources RESTful API
-----------------------------------------------------------
"""

from flask_marshmallow import base_fields
from flask_restplus_patched import Parameters, PatchJSONParameters

from . import schemas
from .models import User


class AddUserParameters(Parameters, schemas.BaseUserSchema):
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


class PatchUserDetailsParameters(PatchJSONParameters):
    # pylint: disable=no-member
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
