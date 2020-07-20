# -*- coding: utf-8 -*-
"""
Input arguments (Parameters) for Passthroughs resources RESTful API
-----------------------------------------------------------
"""

from flask_marshmallow import base_fields
from flask_restplus_patched import PostFormParameters


class CreatePassthroughParameters(PostFormParameters):

    edm_target = base_fields.String(required=True)
