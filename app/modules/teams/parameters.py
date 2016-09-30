# encoding: utf-8
"""
Input arguments (Parameters) for Team resources RESTful API
-----------------------------------------------------------
"""

from flask_marshmallow import base_fields
from flask_restplus_patched import PostFormParameters, PatchJSONParameters

from . import schemas
from .models import Team


class CreateTeamParameters(PostFormParameters, schemas.BaseTeamSchema):

    class Meta(schemas.BaseTeamSchema.Meta):
        # This is not supported yet: https://github.com/marshmallow-code/marshmallow/issues/344
        required = (
            Team.title.key,
        )


class PatchTeamDetailsParameters(PatchJSONParameters):
    # pylint: disable=abstract-method,missing-docstring
    OPERATION_CHOICES = (
        PatchJSONParameters.OP_REPLACE,
    )

    PATH_CHOICES = tuple(
        '/%s' % field for field in (
            Team.title.key,
        )
    )


class AddTeamMemberParameters(PostFormParameters):
    user_id = base_fields.Integer(required=True)
    is_leader = base_fields.Boolean(required=False)
