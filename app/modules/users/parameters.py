# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-order
"""
Input arguments (Parameters) for User resources RESTful API
-----------------------------------------------------------
"""

from flask_login import current_user
from flask_marshmallow import base_fields
from flask_restplus_patched import Parameters, PostFormParameters, PatchJSONParameters
from flask_restplus._http import HTTPStatus
from marshmallow import validates_schema, ValidationError

from app.extensions.api.parameters import PaginationParameters
from app.extensions.api import abort

from . import schemas, permissions
from .models import User


class ListUserParameters(PaginationParameters):
    """
    New user creation (sign up) parameters.
    """

    search = base_fields.String(description='Example: search@email.com', required=False)


class CreateUserParameters(Parameters, schemas.BaseUserSchema):
    """
    New user creation (sign up) parameters.
    """

    # username = base_fields.String(description="Example: root", required=True)

    email = base_fields.Email(description='Example: root@gmail.com', required=True)
    password = base_fields.String(description='No rules yet', required=False)

    # recaptcha_key = base_fields.String(
    #     description=(
    #         "See `/users/signup-form` for details. It is required for everybody, except admins"
    #     ),
    #     required=False
    # )

    class Meta(schemas.BaseUserSchema.Meta):
        fields = schemas.BaseUserSchema.Meta.fields + (
            'email',
            'password',
            # 'recaptcha_key',
        )

    # @validates_schema
    # def validate_captcha(self, data):
    #     """"
    #     Check reCAPTCHA if necessary.

    #     NOTE: we remove 'recaptcha_key' from data once checked because we don't need it
    #     in the resource
    #     """
    #     recaptcha_key = data.pop('recaptcha_key', None)
    #     captcha_is_valid = False
    #     if not recaptcha_key:
    #         no_captcha_permission = permissions.AdminRolePermission()
    #         if no_captcha_permission.check():
    #             captcha_is_valid = True
    #     # NOTE: This hardcoded CAPTCHA key is just for demo purposes.
    #     elif recaptcha_key == 'secret_key':
    #         captcha_is_valid = True

    #     if not captcha_is_valid:
    #         abort(code=HTTPStatus.FORBIDDEN, message="CAPTCHA key is incorrect.")


class CheckinUserParameters(Parameters):
    users_lite = base_fields.List(base_fields.Integer, required=True)


class DeleteUserParameters(Parameters):
    """
    New user creation (sign up) parameters.
    """

    user_guid = base_fields.UUID(description='The GUID of the user', required=True)


class PatchUserDetailsParameters(PatchJSONParameters):
    # pylint: disable=abstract-method
    """
    User details updating parameters following PATCH JSON RFC.
    """

    PATH_CHOICES = tuple(
        '/%s' % field
        for field in (
            'current_password',
            User.email.key,
            User.password.key,
            User.full_name.key,
            User.website.key,
            User.location.key,
            User.affiliation.key,
            User.forum_id.key,
            User.accepted_user_agreement.key,
            User.use_usa_date_format.key,
            User.show_email_in_profile.key,
            User.receive_notification_emails.key,
            User.receive_newsletter_emails.key,
            User.shares_data.key,
            User.last_seen.key,
            User.date_created.key,
            User.last_modified.key,
            User.default_identification_catalogue.key,
            User.profile_asset_guid.key,
            User.footer_logo_asset_guid.key,
            User.is_active.fget.__name__,
            User.is_staff.fget.__name__,
            User.is_admin.fget.__name__,
            User.in_beta.fget.__name__,
            User.in_alpha.fget.__name__,
        )
    )

    SENSITIVE_PATH_CHOICES = tuple(
        '/%s' % field for field in (User.email.key, User.password.key,)
    )

    ADMIN_PATH_CHOICES = tuple(
        '/%s' % field
        for field in (
            User.is_active.fget.__name__,
            User.is_staff.fget.__name__,
            User.is_admin.fget.__name__,
            User.in_beta.fget.__name__,
            User.in_alpha.fget.__name__,
        )
    )

    @classmethod
    def test(cls, obj, field, value, state):
        """
        Additional check for 'current_password' as User hasn't field 'current_password'
        """
        if field == 'current_password':
            if (
                current_user.password != value and obj.password != value
            ):  # pylint: disable=consider-using-in
                abort(code=HTTPStatus.FORBIDDEN, message='Wrong password')
            else:
                state['current_password'] = value
                return True
        return PatchJSONParameters.test(obj, field, value, state)

    @classmethod
    def replace(cls, obj, field, value, state):
        """
        Some fields require extra permissions to be changed.

        Changing `is_active` and `is_staff` properties, current user
        must be a supervisor of the changing user, and `current_password` of
        the current user should be provided.

        Changing `is_admin` property requires current user to be Admin, and
        `current_password` of the current user should be provided..
        """
        if field in cls.SENSITIVE_PATH_CHOICES:
            if 'current_password' not in state:
                raise ValidationError(
                    'Updating sensitive user settings requires `current_password` test operation '
                    'performed before replacements.'
                )

        # if field in {User.is_active.fget.__name__, User.is_staff.fget.__name__}:
        #     context = permissions.SupervisorRolePermission(
        #         obj=obj,
        #         password_required=True,
        #         password=state['current_password']
        #     )
        #     with context:
        #         # Access granted
        #         pass

        if field in cls.ADMIN_PATH_CHOICES:
            if not current_user.is_admin:
                raise ValidationError(
                    'Updating administrator-only user settings requires the logged in user to be an administrator'
                )

                # context = permissions.AdminRolePermission(
                #     password_required=True,
                #     password=state['current_password']
                # )
                # with context:
                #     # Access granted
                #     pass

        return super(PatchUserDetailsParameters, cls).replace(obj, field, value, state)
