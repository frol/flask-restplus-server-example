# -*- coding: utf-8 -*-
"""
Submissions database models
--------------------
"""

import enum
from flask import current_app

from app.extensions import db, TimestampViewed

import logging
import uuid
import os


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class SubmissionMajorType(str, enum.Enum):
    filesystem = 'filesystem'
    archive = 'archive'
    service = 'service'
    test = 'test'

    unknown = 'unknown'
    error = 'error'
    reject = 'reject'


class Submission(db.Model, TimestampViewed):
    """
    Submission database model.

    Submission Structure:
        _db/submissions/<submission GUID>/
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

    major_type = db.Column(
        db.Enum(SubmissionMajorType),
        default=SubmissionMajorType.unknown,
        index=True,
        nullable=False,
    )

    commit = db.Column(db.String(length=40), nullable=True, unique=True)

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

    def init_repository(self):
        return current_app.sub.init_repository(self)

    def get_repository(self):
        return current_app.sub.get_repository(self)

    def git_write_upload_file(self, upload_file):
        repo = self.get_repository()
        file_repo_path = os.path.join(
            repo.working_tree_dir, '_submission', upload_file.filename
        )
        upload_file.save(file_repo_path)
        log.info('Wrote file upload and added to local repo: %r' % (file_repo_path,))

    def git_commit(self, message, update=True):
        repo = self.get_repository()

        repo.index.add('_assets/')
        repo.index.add('_submission/')
        repo.index.add('metadata.json')

        if update:
            self.update_asset_symlinks()

        repo.index.commit(message)

    def update_asset_symlinks(self):
        """
        Traverse the files in the _submission/ folder and add/update symlinks
        for any relevant files we identify

        Ref:
            https://pypi.org/project/python-magic/
        """
        import magic

        pass

    def git_push(self):
        repo = self.get_repository()

        # Get remote URL
        original_url = repo.remotes.origin.url

        # Update remote URL with PAT
        remote_personal_access_token = current_app.config.get(
            'GITLAB_REMOTE_LOGIN_PAT', None
        )
        push_url = original_url.replace(
            'https://', 'https://oauth2:%s@' % (remote_personal_access_token,)
        )
        repo.remotes.origin.set_url(push_url)

        # PUSH
        log.info('Pushing to authorized URL: %r' % (original_url,))
        repo.git.push('--set-upstream', repo.remotes.origin, repo.head.ref)
        log.info(
            '...pushed to %s' % (repo.head.ref),
        )

        # Reset URL on remote
        repo.remotes.origin.set_url(original_url)

    def get_absolute_path(self):
        submissions_database_path = current_app.config.get(
            'SUBMISSIONS_DATABASE_PATH', None
        )
        assert submissions_database_path is not None
        assert os.path.exists(submissions_database_path)

        submission_path = os.path.join(submissions_database_path, str(self.guid))

        return submission_path

    @property
    def absolute_filepath(self):
        asset_path = current_app.config.get('SUBMISSION_DATABASE_PATH', None)
        asset_filname = '%s%s' % (
            self.code,
            self.ext,
        )
        asset_filepath = os.path.join(
            asset_path,
            asset_filname,
        )

        asset_filepath = os.path.abspath(asset_filepath)
        assert os.path.exists(asset_filepath)
        return asset_filepath
