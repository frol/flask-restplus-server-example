# -*- coding: utf-8 -*-
"""
Serialization schemas for Collaborations resources RESTful API
----------------------------------------------------
"""

# from flask_marshmallow import base_fields
from flask_restplus_patched import ModelSchema

from .models import Collaboration


class BaseCollaborationSchema(ModelSchema):
    """
    Base Collaboration schema exposes only the most general fields.
    """

    class Meta:
        # pylint: disable=missing-docstring
        model = Collaboration
        fields = (
            Collaboration.guid.key,
            Collaboration.title.key,
        )
        dump_only = (Collaboration.guid.key,)


class DetailedCollaborationSchema(BaseCollaborationSchema):
    """
    Detailed Collaboration schema exposes all useful fields.
    """

    class Meta(BaseCollaborationSchema.Meta):
        fields = BaseCollaborationSchema.Meta.fields + (
            Collaboration.created.key,
            Collaboration.updated.key,
        )
        dump_only = BaseCollaborationSchema.Meta.dump_only + (
            Collaboration.created.key,
            Collaboration.updated.key,
        )
