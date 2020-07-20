# -*- coding: utf-8 -*-
"""
Input arguments (Parameters) for Collaborations resources RESTful API
-----------------------------------------------------------
"""

# from flask_marshmallow import base_fields
from flask_restplus_patched import PostFormParameters, PatchJSONParameters

from . import schemas
from .models import Collaboration


class CreateCollaborationParameters(
    PostFormParameters, schemas.DetailedCollaborationSchema
):
    class Meta(schemas.DetailedCollaborationSchema.Meta):
        pass


class PatchCollaborationDetailsParameters(PatchJSONParameters):
    # pylint: disable=abstract-method,missing-docstring
    OPERATION_CHOICES = (PatchJSONParameters.OP_REPLACE,)

    PATH_CHOICES = tuple('/%s' % field for field in (Collaboration.title.key,))
