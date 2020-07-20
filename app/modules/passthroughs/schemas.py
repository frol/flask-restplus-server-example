# -*- coding: utf-8 -*-
"""
Serialization schemas for Passthroughs resources RESTful API
----------------------------------------------------
"""

from flask_marshmallow import base_fields
from flask_restplus_patched import ModelSchema


class BasePassthroughSchema(ModelSchema):
    """
    Base Passthrough schema exposes only the most general fields.
    """

    edm_target = base_fields.String(required=True)
