# -*- coding: utf-8 -*-
"""
Submissions database models
--------------------
"""

from sqlalchemy_utils import Timestamp

from app.extensions import db

import uuid


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
