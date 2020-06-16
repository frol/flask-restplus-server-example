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
            User.guid.key,
            User.email.key,
            User.full_name.key,
            User.affiliation.key,
            User.location.key,
            User.profile_asset_guid.key,
            User.is_active.fget.__name__,
            User.is_staff.fget.__name__,
            User.is_admin.fget.__name__,
        )
        dump_only = (User.guid.key,)


class DetailedUserPermissionsSchema(ModelSchema):
    class Meta:
        # pylint: disable=missing-docstring
        model = User
        fields = (User.guid.key,)
        dump_only = (User.guid.key,)


class DetailedUserSchema(BaseUserSchema):
    """ Detailed user schema exposes all fields used to render a normal user profile. """

    class Meta(BaseUserSchema.Meta):
        fields = BaseUserSchema.Meta.fields + (
            User.last_seen.key,
            User.date_created.key,
            User.forum_id.key,
            User.website.key,
        )

class PersonalUserSchema(DetailedUserSchema):
    """ Personal user schema exposes all fields needed to render a user profile
    that can be edited by the currently logged in user. """

    class Meta(DetailedUserSchema.Meta):
        fields = DetailedUserSchema.Meta.fields + (
            User.default_identification_catalogue.key,
            User.footer_logo_asset_guid.key,
            User.shares_data.key,
            User.receive_newsletter_emails.key,
            User.receive_notification_emails.key,
            User.show_email_in_profile.key,
            User.use_usa_date_format.key,
            User.accepted_user_agreement.key,
        )

class UserSignupFormSchema(Schema):
    recaptcha_server_key = base_fields.String(required=True)
