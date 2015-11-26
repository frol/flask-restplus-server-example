# encoding: utf-8
"""
Input arguments (Parameters) for Team resources RESTful API
===========================================================
"""

from flask_restplus_patched import Parameters, PatchJSONParameters

from . import schemas
from .models import Team


class CreateTeamParameters(Parameters, schemas.BaseTeamSchema):

    class Meta(schemas.BaseTeamSchema):
        required = (
            Team.title.key,
        )


class PatchTeamDetailsParameters(PatchJSONParameters):
    PATH_CHOICES = tuple(
        '/%s' % field for field in (
            Team.title.key,
            Team.members.key,
        )
    )
