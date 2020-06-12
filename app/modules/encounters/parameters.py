# encoding: utf-8
"""
Input arguments (Parameters) for Encounters resources RESTful API
-----------------------------------------------------------
"""

from flask_marshmallow import base_fields
from flask_restplus_patched import PostFormParameters, PatchJSONParameters

from . import schemas
from .models import Encounter


class CreateEncounterParameters(PostFormParameters, schemas.DetailedEncounterSchema):

    class Meta(schemas.DetailedEncounterSchema.Meta):
        pass


class PatchEncounterDetailsParameters(PatchJSONParameters):
    # pylint: disable=abstract-method,missing-docstring
    OPERATION_CHOICES = (
        PatchJSONParameters.OP_REPLACE,
    )

    PATH_CHOICES = tuple(
        '/%s' % field for field in (
            Encounter.title.key,
        )
    )
