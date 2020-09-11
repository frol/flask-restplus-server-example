# -*- coding: utf-8 -*-
"""
Assets database models
--------------------
"""
from flask import current_app
import os

from app.extensions import db, TimestampViewed

import uuid


class Asset(db.Model, TimestampViewed):
    """
    Assets database model.
    """

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name

    ext = db.Column(db.String, index=True, nullable=False)
    mime_type = db.Column(db.String, index=True, nullable=False)

    title = db.Column(db.String(length=128), nullable=True)
    description = db.Column(db.String(length=255), nullable=True)

    meta = db.Column(db.JSON, nullable=True)

    submission_guid = db.Column(
        db.GUID, db.ForeignKey('submission.guid'), index=True, nullable=False
    )
    submission = db.relationship('Submission', backref=db.backref('assets'))

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
            'file="{self.guid}{self.ext}"'
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
