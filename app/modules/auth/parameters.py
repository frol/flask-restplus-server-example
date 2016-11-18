# encoding: utf-8
# pylint: disable=wrong-import-order
"""
Input arguments (Parameters) for Auth resources RESTful API
-----------------------------------------------------------
"""
from flask_login import current_user
from flask_marshmallow import base_fields
from flask_restplus_patched import PostFormParameters
from marshmallow import validates, ValidationError

from app.extensions import api
from app.extensions.api.parameters import PaginationParameters


class ListOAuth2ClientsParameters(PaginationParameters):
    user_id = base_fields.Integer(required=True)

    @validates('user_id')
    def validate_user_id(self, data):
        if current_user.id != data:
            raise ValidationError("It is only allowed to query your own OAuth2 clients.")


class CreateOAuth2ClientParameters(PostFormParameters):
    redirect_uris = base_fields.List(base_fields.String, required=False)
    default_scopes = base_fields.List(base_fields.String, required=True)

    @validates('default_scopes')
    def validate_default_scopes(self, data):
        unknown_scopes = set(data) - set(api.api_v1.authorizations['oauth2_password']['scopes'])
        if unknown_scopes:
            raise ValidationError("'%s' scope(s) are not supported." % (', '.join(unknown_scopes)))
