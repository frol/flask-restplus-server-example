# encoding: utf-8

from flask.ext.marshmallow import base_fields

from flask_restplus_patched import Schema, ModelSchema
from .models import User


class BaseUserSchema(ModelSchema):

    class Meta:
        model = User
        fields = (
            User.id.key,
            User.username.key,
            User.first_name.key,
            User.middle_name.key,
            User.last_name.key,
        )
        dump_only = (
            User.id.key,
        )


class DetailedUserSchema(BaseUserSchema):

    class Meta(BaseUserSchema.Meta):
        fields = BaseUserSchema.Meta.fields + (
            User.email.key,
        )

        
class UserSignupFormSchema(Schema):
    
    recaptcha_server_key = base_fields.String(required=True)
