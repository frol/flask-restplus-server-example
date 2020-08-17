# -*- coding: utf-8 -*-
"""
Assets database models
--------------------
"""
from flask import current_app
import os

from app.extensions import db, TimestampViewed

import uuid


class Submission(db.Model, TimestampViewed):
    """
    Assets database model.
    """

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name

    _hash =

    title =
    description =
    metadata =

    submitter_guid =
    submitter =

    owner_guid =
    owner =

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
            'file="{self.code}{self.ext}"'
            ')>'.format(class_name=self.__class__.__name__, self=self)
        )

    @property
    def absolute_filepath(self):
        asset_path = current_app.config.get('SUBMISSION_DATABASE_PATH', None)
        asset_filname = '%s%s' % (self.code, self.ext,)
        asset_filepath = os.path.join(asset_path, asset_filname,)

        asset_filepath = os.path.abspath(asset_filepath)
        assert os.path.exists(asset_filepath)
        return asset_filepath


class Asset(db.Model, TimestampViewed):
    """
    Assets database model.
    """

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name
    description =
    metadata =

    submission_guid =
    submission

    ext = db.Column(db.String(length=5), nullable=False)

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
            'file="{self.code}{self.ext}"'
            ')>'.format(class_name=self.__class__.__name__, self=self)
        )

    @property
    def absolute_filepath(self):
        asset_path = current_app.config.get('ASSET_DATABASE_PATH', None)
        asset_filname = '%s%s' % (self.code, self.ext,)
        asset_filepath = os.path.join(asset_path, asset_filname,)

        asset_filepath = os.path.abspath(asset_filepath)
        assert os.path.exists(asset_filepath)
        return asset_filepath
