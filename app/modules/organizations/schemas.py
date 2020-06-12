# encoding: utf-8
"""
Serialization schemas for Organizations resources RESTful API
----------------------------------------------------
"""

from flask_marshmallow import base_fields
from flask_restplus_patched import ModelSchema

from .models import Organization


class BaseOrganizationSchema(ModelSchema):
    """
    Base Organization schema exposes only the most general fields.
    """

    class Meta:
        # pylint: disable=missing-docstring
        model = Organization
        fields = (
            Organization.guid.key,
            Organization.title.key,
        )
        dump_only = (
            Organization.guid.key,
        )


class DetailedOrganizationSchema(BaseOrganizationSchema):
    """
    Detailed Organization schema exposes all useful fields.
    """

    class Meta(BaseOrganizationSchema.Meta):
        fields = BaseOrganizationSchema.Meta.fields + (
            Organization.created.key,
            Organization.updated.key,
        )
        dump_only = BaseOrganizationSchema.Meta.dump_only + (
            Organization.created.key,
            Organization.updated.key,
        )