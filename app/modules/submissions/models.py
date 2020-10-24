# -*- coding: utf-8 -*-
"""
Submissions database models
--------------------
"""

import enum
from flask import current_app

from app.extensions import db, TimestampViewed, parallel

from app.modules.assets.models import Asset
from app.version import version

import logging
import tqdm
import uuid
import json
import git
import os


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def compute_xxhash64_digest_filepath(filepath):
    try:
        import xxhash
        import os

        assert os.path.exists(filepath)

        with open(filepath, 'rb') as file_:
            digest = xxhash.xxh64_hexdigest(file_.read())
    except Exception:
        digest = None
    return digest


class GitLabPAT(object):
    def __init__(self, repo=None, url=None):
        assert repo is not None or url is not None, 'Must specify one of repo or url'

        self.repo = repo
        if url is None:
            assert repo is not None
            url = repo.remotes.origin.url
        self.original_url = url

        remote_personal_access_token = current_app.config.get(
            'GITLAB_REMOTE_LOGIN_PAT', None
        )
        self.authenticated_url = self.original_url.replace(
            'https://', 'https://oauth2:%s@' % (remote_personal_access_token,)
        )

    def __enter__(self):
        # Update remote URL with PAT
        if self.repo is not None:
            self.repo.remotes.origin.set_url(self.authenticated_url)
        return self

    def __exit__(self, type, value, traceback):
        if self.repo is not None:
            self.repo.remotes.origin.set_url(self.original_url)
        return True


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
    commit_mime_whitelist_guid = db.Column(db.GUID, index=True, nullable=True)
    commit_houston_api_version = db.Column(db.String, index=True, nullable=True)

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

    def ensure_repository(self):
        return current_app.sub.ensure_repository(self)

    def get_repository(self):
        return current_app.sub.get_repository(self)

    def git_write_upload_file(self, upload_file):
        repo = self.get_repository()
        file_repo_path = os.path.join(
            repo.working_tree_dir, '_submission', upload_file.filename
        )
        upload_file.save(file_repo_path)
        log.info('Wrote file upload and added to local repo: %r' % (file_repo_path,))

    def git_commit(self, message, realize=True, update=True):
        repo = self.get_repository()

        if realize:
            self.realize_submission()

        if update:
            self.update_asset_symlinks()

        submission_path = self.get_absolute_path()
        submission_metadata_path = os.path.join(submission_path, 'metadata.json')

        assert os.path.exists(submission_metadata_path)
        with open(submission_metadata_path, 'r') as submission_metadata_file:
            submission_metadata = json.load(submission_metadata_file)

        submission_metadata['commit_mime_whitelist_guid'] = str(
            current_app.sub.mime_type_whitelist_guid
        )
        submission_metadata['commit_houston_api_version'] = str(version)

        with open(submission_metadata_path, 'w') as submission_metadata_file:
            json.dump(submission_metadata, submission_metadata_file)

        repo.index.add('_assets/')
        repo.index.add('_submission/')
        repo.index.add('metadata.json')

        commit = repo.index.commit(message)

        self.update_metadata_from_commit(commit)

    def git_push(self):
        repo = self.get_repository()
        assert repo is not None

        with GitLabPAT(repo):
            log.info('Pushing to authorized URL')
            repo.git.push('--set-upstream', repo.remotes.origin, repo.head.ref)
            log.info('...pushed to %s' % (repo.head.ref,))

        return repo

    def git_pull(self):
        repo = self.get_repository()
        assert repo is not None

        with GitLabPAT(repo):
            log.info('Pulling from authorized URL')
            repo.git.pull(repo.remotes.origin, repo.head.ref)
            log.info('...pulled')

        self.update_metadata_from_repo(repo)

        return repo

    def git_clone(self, project):
        repo = self.get_repository()
        assert repo is None

        submission_abspath = self.get_absolute_path()
        gitlab_url = project.web_url

        with GitLabPAT(url=gitlab_url) as glpat:
            args = (
                gitlab_url,
                submission_abspath,
            )
            log.info('Cloning remote submission:\n\tremote: %r\n\tlocal:  %r' % args)
            glpat.repo = git.Repo.clone_from(glpat.authenticated_url, submission_abspath)
            log.info('...cloned')

        repo = self.get_repository()
        assert repo is not None

        self.update_metadata_from_project(project)
        self.update_metadata_from_repo(repo)

        return repo

    def realize_submission(self):
        """
        Unpack any archives and resolve any symlinks

        Must check for security vulnerabilities around decompression bombs and
        recursive links
        """
        ARCHIVE_MIME_TYPE_WHITELIST = [  # NOQA
            'application/gzip',
            'application/vnd.rar',
            'application/x-7z-compressed',
            'application/x-bzip',
            'application/x-bzip2',
            'application/x-tar',
            'application/zip',
        ]
        pass

    def update_asset_symlinks(self, verbose=True):
        """
        Traverse the files in the _submission/ folder and add/update symlinks
        for any relevant files we identify

        Ref:
            https://pypi.org/project/python-magic/
            https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
            http://www.iana.org/assignments/media-types/media-types.xhtml
        """
        import magic
        import utool as ut

        submission_abspath = self.get_absolute_path()
        submission_path = os.path.join(submission_abspath, '_submission')
        assets_path = os.path.join(submission_abspath, '_assets')

        # Walk the submission path, looking for white-listed MIME type files
        files = []
        skipped = []
        errors = []
        walk_list = list(os.walk(submission_path))
        print('Walking submission...')
        for root, directories, filenames in tqdm.tqdm(walk_list):
            for filename in filenames:
                filepath = os.path.join(root, filename)

                # Normalize path (sanity check)
                filepath = os.path.normpath(filepath)

                # Sanity check, ensure that the path is formatted well
                assert os.path.exists(filepath)
                assert os.path.isabs(filepath)
                try:
                    basename = os.path.basename(filepath)
                    _, extension = os.path.splitext(basename)
                    extension = extension.lower()

                    if basename.startswith('.'):
                        # Skip hidden files
                        if basename not in ['.touch']:
                            skipped.append((filepath, basename))
                        continue

                    if os.path.isdir(filepath):
                        # Skip any directories (sanity check)
                        skipped.append((filepath, extension))
                        continue

                    if os.path.islink(filepath):
                        # Skip any symbolic links (sanity check)
                        skipped.append((filepath, extension))
                        continue

                    mime_type = magic.from_file(filepath, mime=True)
                    if mime_type not in current_app.sub.mime_type_whitelist:
                        # Skip any unsupported MIME types
                        skipped.append((filepath, extension))
                        continue

                    magic_signature = magic.from_file(filepath)
                    size_bytes = os.path.getsize(filepath)

                    file_data = {
                        'filepath': filepath,
                        'extension': extension,
                        'mime_type': mime_type,
                        'magic_signature': magic_signature,
                        'size_bytes': size_bytes,
                        'submission_guid': self.guid,
                    }
                    files.append(file_data)
                except Exception:
                    errors.append(filepath)

        if verbose:
            print('Processed asset files from submission: %r' % (self,))
            print('\tFiles   : %d' % (len(files),))
            print('\tSkipped : %d' % (len(skipped),))
            if len(skipped) > 0:
                skipped_ext_list = [skip[1] for skip in skipped]
                skipped_ext_str = ut.repr3(ut.dict_hist(skipped_ext_list))
                skipped_ext_str = skipped_ext_str.replace('\n', '\n\t\t')
                print('\t\t%s' % (skipped_ext_str,))
            print('\tErrors  : %d' % (len(errors),))

        # Compute the xxHash64 for all found files
        filepath_list = [file_data['filepath'] for file_data in files]
        arguments_list = list(zip(filepath_list))
        print('Computing filesystem xxHash64...')
        filesystem_xxhash64_list = parallel(
            compute_xxhash64_digest_filepath, arguments_list
        )
        filesystem_guid_list = list(map(ut.hashable_to_uuid, filesystem_xxhash64_list))

        # Update file_data with the filesystem and semantic hash information
        zipped = zip(files, filesystem_xxhash64_list, filesystem_guid_list)
        for file_data, filesystem_xxhash64, filesystem_guid in zipped:
            file_data['filesystem_xxhash64'] = filesystem_xxhash64
            file_data['filesystem_guid'] = filesystem_guid
            semantic_guid_data = (
                file_data['submission_guid'],
                file_data['filesystem_guid'],
            )
            file_data['semantic_guid'] = ut.hashable_to_uuid(semantic_guid_data)

        # Add new or update any existing Assets found in the Submission
        asset_submission_filepath_list = [
            file_data.pop('filepath', None) for file_data in files
        ]
        assets = []
        with db.session.begin():
            for file_data in files:
                semantic_guid = file_data.get('semantic_guid', None)
                asset = Asset.query.filter(Asset.semantic_guid == semantic_guid).first()
                if asset is None:
                    # Create record if asset is new
                    asset = Asset(**file_data)
                    db.session.add(asset)
                else:
                    # Update record if Asset exists
                    for key in file_data:
                        if key in ['submission_guid', 'filesystem_guid', 'semantic_guid']:
                            continue
                        value = file_data[key]
                        setattr(asset, key, value)
                    db.session.merge(asset)
                assets.append(asset)

        # Delete all existing symlinks
        existing_asset_symlinks = ut.glob(os.path.join(assets_path, '*'))
        for existing_asset_symlink in existing_asset_symlinks:
            basename = os.path.basename(existing_asset_symlink)
            if basename in ['.touch']:
                continue
            os.remove(existing_asset_symlink)

        # Update all symlinks for each Asset
        for asset, asset_submission_filepath in zip(
            assets, asset_submission_filepath_list
        ):
            db.session.refresh(asset)
            asset.update_symlink(asset_submission_filepath)
            if verbose:
                print(filepath)
                print('\tAsset         : %s' % (asset,))
                print('\tSemantic GUID : %s' % (asset.semantic_guid,))
                print('\tExtension     : %s' % (asset.extension,))
                print('\tMIME type     : %s' % (asset.mime_type,))
                print('\tSignature     : %s' % (asset.magic_signature,))
                print('\tSize bytes    : %s' % (asset.size_bytes,))
                print('\tFS xxHash64   : %s' % (asset.filesystem_xxhash64,))
                print('\tFS GUID       : %s' % (asset.filesystem_guid,))

        # Get all historical and current Assets for this Submission
        db.session.refresh(self)

        # Delete any historical Assets that have been deleted from this commit
        deleted_assets = list(set(self.assets) - set(assets))
        if verbose:
            print('Deleting %d orphaned Assets' % (len(deleted_assets),))
        with db.session.begin():
            for deleted_asset in deleted_assets:
                deleted_asset.delete()
        db.session.refresh(self)

    def update_metadata_from_project(self, project):
        # Update any local metadata from sub
        for tag in project.tag_list:
            tag = tag.strip().split(':')
            if len(tag) == 2:
                key, value = tag
                key_ = key.lower()
                value_ = value.lower()
                if key_ == 'type':
                    default_major_type = SubmissionMajorType.unknown
                    self.major_type = getattr(
                        SubmissionMajorType, value_, default_major_type
                    )

        self.description = project.description
        with db.session.begin():
            db.session.merge(self)
        db.session.refresh(self)

    def update_metadata_from_repo(self, repo):
        repo = self.get_repository()
        assert repo is not None

        if len(repo.branches) > 0:
            commit = repo.branches.master.commit
            self.update_metadata_from_commit(commit)

        return repo

    def update_metadata_from_commit(self, commit):
        with db.session.begin():
            self.commit = commit.hexsha
            self.commit_mime_whitelist_guid = current_app.sub.mime_type_whitelist_guid
            self.commit_houston_api_version = version
            db.session.merge(self)
        db.session.refresh(self)

    def get_absolute_path(self):
        submissions_database_path = current_app.config.get(
            'SUBMISSIONS_DATABASE_PATH', None
        )
        assert submissions_database_path is not None
        assert os.path.exists(submissions_database_path)

        submission_path = os.path.join(submissions_database_path, str(self.guid))

        return submission_path

    def delete(self):
        for asset in self.assets:
            asset.delete()
        db.session.refresh(self)
        with db.session.begin():
            db.session.delete(self)

    @property
    def absolute_filepath(self):
        asset_path = current_app.config.get('SUBMISSION_DATABASE_PATH', None)
        asset_filname = '%s%s' % (
            self.guid,
            self.extension,
        )
        asset_filepath = os.path.join(
            asset_path,
            asset_filname,
        )

        asset_filepath = os.path.abspath(asset_filepath)
        assert os.path.exists(asset_filepath)
        return asset_filepath
