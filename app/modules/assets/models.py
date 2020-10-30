# -*- coding: utf-8 -*-
"""
Assets database models
--------------------
"""
# from flask import current_app
from functools import total_ordering
import os

from app.extensions import db, HoustonModel

import uuid


@total_ordering
class Asset(db.Model, HoustonModel):
    """
    Assets database model.
    """

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name

    extension = db.Column(db.String, index=True, nullable=False)

    mime_type = db.Column(db.String, index=True, nullable=False)
    magic_signature = db.Column(db.String, nullable=False)

    size_bytes = db.Column(db.BigInteger)

    filesystem_xxhash64 = db.Column(db.String, nullable=False)
    filesystem_guid = db.Column(db.GUID, nullable=False)
    semantic_guid = db.Column(
        db.GUID, nullable=False, unique=True
    )  # must be unique for (submission.guid, asset.filesystem_guid)
    content_guid = db.Column(db.GUID, nullable=True)

    title = db.Column(db.String(length=128), nullable=True)
    description = db.Column(db.String(length=255), nullable=True)

    meta = db.Column(db.JSON, nullable=True)

    submission_guid = db.Column(
        db.GUID,
        db.ForeignKey('submission.guid', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    submission = db.relationship('Submission', backref=db.backref('assets'))

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
            'filesystem_guid={self.filesystem_guid}, '
            'semantic_guid={self.semantic_guid}, '
            'mime="{self.mime_type}", '
            ')>'.format(class_name=self.__class__.__name__, self=self)
        )

    def __eq__(self, other):
        return self.guid == other.guid

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return str(self.guid) < str(other.guid)

    def __hash__(self):
        return hash(self.guid)

    def get_symlink(self):
        submission_abspath = self.submission.get_absolute_path()
        assets_path = os.path.join(submission_abspath, '_assets')

        asset_symlink_filename = '%s.%s' % (
            self.guid,
            self.extension,
        )
        asset_symlink_filepath = os.path.join(assets_path, asset_symlink_filename)

        return asset_symlink_filepath

    def update_symlink(self, asset_submission_filepath):
        assert os.path.exists(asset_submission_filepath)

        asset_symlink_filepath = self.get_symlink()
        if os.path.exists(asset_symlink_filepath):
            os.remove(asset_symlink_filepath)

        submission_abspath = self.submission.get_absolute_path()
        asset_submission_filepath_relative = asset_submission_filepath.replace(
            submission_abspath, '..'
        )
        os.symlink(asset_submission_filepath_relative, asset_symlink_filepath)
        assert os.path.exists(asset_symlink_filepath)
        assert os.path.islink(asset_symlink_filepath)

        return asset_symlink_filepath

    def delete(self):
        with db.session.begin():
            db.session.delete(self)
