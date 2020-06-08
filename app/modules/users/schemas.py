# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods
"""
User schemas
------------
"""

from flask_marshmallow import base_fields
from flask_restplus_patched import Schema, ModelSchema

from .models import User


class BaseUserSchema(ModelSchema):
    """
    Base user schema exposes only the most general fields.
    """

    class Meta:
        # pylint: disable=missing-docstring
        model = User
        fields = (
            User.id.key,
            User.email.key,
            User.first_name.key,
            User.middle_name.key,
            User.last_name.key,
            User.suffix_name.key,
            # User.username.key,
            User.is_active.fget.__name__,
            User.is_staff.fget.__name__,
            User.is_admin.fget.__name__,
        )
        dump_only = (User.id.key,)


class DetailedUserPermissionsSchema(ModelSchema):
    class Meta:
        # pylint: disable=missing-docstring
        model = User
        fields = (User.id.key,)
        dump_only = (User.id.key,)


class DetailedUserSchema(BaseUserSchema):
    """ Detailed user schema exposes all useful fields. """

    class Meta(BaseUserSchema.Meta):
        fields = BaseUserSchema.Meta.fields + (
            User.is_email_confirmed.fget.__name__,
            User.birth_month.key,
            User.birth_year.key,
            User.age.fget.__name__,
            User.phone.key,
            User.address_line1.key,
            User.address_line2.key,
            User.address_city.key,
            User.address_state.key,
            User.address_zip.key,
            User.created.key,
            User.updated.key,
            User.in_beta.fget.__name__,
            User.in_alpha.fget.__name__,
            User.picture.fget.__name__,
        )


class UserSignupFormSchema(Schema):
    recaptcha_server_key = base_fields.String(required=True)
