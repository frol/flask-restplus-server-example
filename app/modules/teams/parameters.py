# encoding: utf-8
"""
Input arguments (Parameters) for Team resources RESTful API
-----------------------------------------------------------
"""

from flask_marshmallow import base_fields
from flask_restplus_patched import Parameters, PatchJSONParameters

from . import schemas
from .models import Team


class CreateTeamParameters(Parameters, schemas.BaseTeamSchema):

    class Meta(schemas.BaseTeamSchema.Meta):
        # This is not supported yet: https://github.com/marshmallow-code/marshmallow/issues/344
        required = (
            Team.title.key,
        )


class PatchTeamDetailsParameters(PatchJSONParameters):
    PATH_CHOICES = tuple(
        '/%s' % field for field in (
            Team.title.key,
        )
    )


class AddTeamMemberParameters(Parameters):
    user_id = base_fields.Integer(required=True)
    is_leader = base_fields.Boolean(required=False)
