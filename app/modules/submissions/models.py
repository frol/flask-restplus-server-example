# -*- coding: utf-8 -*-
"""
Submissions database models
--------------------
"""

import enum
from flask import current_app

from app.extensions import db, TimestampViewed

import uuid
import os


class SubmissionMajorType(str, enum.Enum):
    filesystem = 'filesystem'
    archive = 'archive'
    service = 'service'

    unknown = 'unknown'
    error = 'error'
    reject = 'reject'


class Submission(db.Model, TimestampViewed):
    """
    Submission database model.

    Submission Structure:
        _submissions/<submission GUID>/
        - .git/
        - _submission/
        - - <user's uploaded data>
        - _assets/
        - - <symlinks into _submission/ folder> with name <asset GUID >.ext --> ../_submissions/path/to/asset/original_name.ext
        - metadata.json
    """

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name

    submission_major_type = db.Column(db.Enum(SubmissionMajorType), nullable=True)

    commit = db.Column(db.String(length=40), nullable=False, unique=True)

    title = db.Column(db.String(length=128), nullable=True)
    description = db.Column(db.String(length=255), nullable=True)

    meta = db.Column(db.JSON, nullable=True)

    owner_guid = db.Column(
        db.GUID, db.ForeignKey('user.guid'), index=True, nullable=False
    )
    owner = db.relationship('User', backref=db.backref('submissions'))

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
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
