from six import itervalues

from flask_restplus_patched import Parameters, JSONParameters, PatchJSONParameters

from app import marshmallow

from . import schemas
from .models import User


class PaginationParameters(Parameters):

    limit = marshmallow.Integer(default=20, missing=20)
    offset = marshmallow.Integer(default=0, missing=0)


class AddUserParameters(JSONParameters, schemas.BaseUserSchema):
    
    username = marshmallow.String(description="Example: root", required=True)
    email = marshmallow.Email(description="Example: root@gmail.com", required=True)
    password = marshmallow.String(description="No rules yet", required=True)
    recaptcha_key = marshmallow.String(
        description=(
            "See `/users/signup_form` for details. It is required for everybody, except admins"
        ),
        required=False
    )

    class Meta:
        exclude = ('id', )


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
