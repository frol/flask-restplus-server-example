# encoding: utf-8
"""
Common reusable Parameters classes
----------------------------------
"""

from marshmallow import validate

from flask_marshmallow import base_fields
from flask_restplus_patched import Parameters


class PaginationParameters(Parameters):
    """
    Helper Parameters class to reuse pagination.
    """

    limit = base_fields.Integer(
        description="limit a number of items (allowed range is 1-100), default is 20.",
        missing=20,
        validate=validate.Range(min=1, max=100)
    )
    offset = base_fields.Integer(
        description="a number of items to skip, default is 0.",
        missing=0,
        validate=validate.Range(min=0)
    )
