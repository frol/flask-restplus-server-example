# -*- coding: utf-8 -*-
"""
Input arguments (Parameters) for Organizations resources RESTful API
-----------------------------------------------------------
"""

# from flask_marshmallow import base_fields
from flask_restplus_patched import PostFormParameters, PatchJSONParameters

from . import schemas
from .models import Organization


class CreateOrganizationParameters(
    PostFormParameters, schemas.DetailedOrganizationSchema
):
    class Meta(schemas.DetailedOrganizationSchema.Meta):
        pass


class PatchOrganizationDetailsParameters(PatchJSONParameters):
    # pylint: disable=abstract-method,missing-docstring
    OPERATION_CHOICES = (PatchJSONParameters.OP_REPLACE,)

    PATH_CHOICES = tuple('/%s' % field for field in (Organization.title.key,))
