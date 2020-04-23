# encoding: utf-8
"""
Serialization schemas for Assets resources RESTful API
----------------------------------------------------
"""

from flask_restplus_patched import ModelSchema

from .models import Asset


class BaseAssetSchema(ModelSchema):
    """
    Base Asset schema exposes only the most general fields.
    """

    class Meta:
        # pylint: disable=missing-docstring
        model = Asset
        fields = (
            Asset.id.key,
            Asset.code.key,
        )
        dump_only = (
            Asset.id.key,
        )


class DetailedAssetSchema(BaseAssetSchema):
    """
    Detailed Asset schema exposes all useful fields.
    """

    class Meta(BaseAssetSchema.Meta):
        fields = BaseAssetSchema.Meta.fields + (
            Asset.ext.key,
            Asset.created.key,
            Asset.updated.key,
        )
        dump_only = BaseAssetSchema.Meta.dump_only + (
            Asset.created.key,
            Asset.updated.key,
        )
