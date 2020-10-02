# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""
Submission Management.

"""
import logging

from flask import current_app, request, session, render_template  # NOQA
from flask_login import current_user  # NOQA
import gitlab
import git
import json
import os
from pathlib import Path

import pytz

import keyword


KEYWORD_SET = set(keyword.kwlist)


log = logging.getLogger(__name__)

PST = pytz.timezone('US/Pacific')


class SubmissionManager(object):
    def __init__(self, app, pre_initialize=False, *args, **kwargs):
        super(SubmissionManager, self).__init__(*args, **kwargs)
        self.initialized = False

        self.app = app
        app.sub = self

        self.gl = None
        self.namespace = None

        if pre_initialize:
            self.ensure_initialed()

    def ensure_initialed(self):
        if not self.initialized:
            assert self.gl is None
            log.info('Logging into Submission GitLab...')
            remote_uri = self.app.config.get('GITLAB_REMOTE_URI', None)
            remote_personal_access_token = self.app.config.get(
                'GITLAB_REMOTE_LOGIN_PAT', None
            )
            remote_namespace = self.app.config.get('GITLAB_NAMESPACE', None)

            self.gl = gitlab.Gitlab(
                remote_uri, private_token=remote_personal_access_token
            )
            self.gl.auth()
            log.info('Logged in: %r' % (self.gl,))

            # Check for namespace
            if remote_namespace is None:
                namespace = self.gl.namespaces.get(id=self.gl.user.id)
            else:
                namespaces = self.gl.namespaces.list(search=remote_namespace)
                if len(namespaces) == 0:
                    path = remote_namespace.lower()
                    group = self.gl.groups.create(
                        {'name': remote_namespace, 'path': path}
                    )
                    namespace = self.gl.namespaces.get(id=group.id)
                    namespaces = self.gl.namespaces.list(search=remote_namespace)
                assert len(namespaces) == 1
                namespace = namespaces[0]

            self.namespace = namespace
            log.info('Using namespace: %r' % (self.namespace,))

            self.initialized = True

    def init_repository(self, submission, remote=True):
        project = None

        if remote:
            self.ensure_initialed()

            projects = self.gl.projects.list(search=str(submission.guid))
            if len(projects) == 1:
                project_ = projects[0]
                if project_.path == str(submission.guid):
                    if project_.namespace['id'] == self.namespace.id:
                        args = (
                            project_.namespace['name'],
                            project_.path,
                        )
                        log.info(
                            'Found existing remote project in GitLab: %r / %r' % args
                        )
                        project = project_

            if project is None:
                args = (
                    self.namespace,
                    submission.guid,
                )
                log.info('Creating remote project in GitLab: %r / %r' % args)
                description = ' - '.join([submission.title, submission.description])
                project = self.gl.projects.create(
                    {
                        'path': str(submission.guid),
                        'description': description,
                        'emails_disabled': True,
                        'namespace_id': self.namespace.id,
                        'visibility': 'private',
                        'merge_method': 'rebase_merge',
                        'lfs_enabled': True,
                        # 'tag_list': [],
                    }
                )

        # Initialize local repo
        submission_path = submission.get_absolute_path()

        submission_git_path = os.path.join(submission_path, '.git')
        submission_sub_path = os.path.join(submission_path, '_submission')
        submission_asset_path = os.path.join(submission_path, '_assets')
        submission_metadata_path = os.path.join(submission_path, 'metadata.json')

        # Submission Repo Structure:
        #     _db/submissions/<submission GUID>/
        #         - .git/
        #         - _submission/
        #         - - <user's uploaded data>
        #         - _assets/
        #         - - <symlinks into _submission/ folder> with name <asset GUID >.ext --> ../_submissions/path/to/asset/original_name.ext
        #         - metadata.json

        if not os.path.exists(submission_path):
            log.info('Creating submissions structure: %r' % (submission_path,))
            os.mkdir(submission_path)

        # Create the repo
        if not os.path.exists(submission_git_path):
            repo = git.Repo.init(submission_path)
            assert len(repo.remotes) == 0
            gitlab_remote_public_name = self.app.config.get('GITLAB_PUBLIC_NAME', None)
            gitlab_remote_email = self.app.config.get('GITLAB_EMAIL', None)
            assert None not in [gitlab_remote_public_name, gitlab_remote_email]
            repo.git.config('user.name', gitlab_remote_public_name)
            repo.git.config('user.email', gitlab_remote_email)
        else:
            repo = git.Repo(submission_path)

        if project is not None:
            if len(repo.remotes) == 0:
                origin = repo.create_remote('origin', project.web_url)
            else:
                origin = repo.remotes.origin
            assert origin.url == project.web_url

        if not os.path.exists(submission_sub_path):
            os.mkdir(submission_sub_path)
        Path(os.path.join(submission_sub_path, '.touch')).touch()

        if not os.path.exists(submission_asset_path):
            os.mkdir(submission_asset_path)
        Path(os.path.join(submission_asset_path, '.touch')).touch()

        if not os.path.exists(submission_metadata_path):
            with open(submission_metadata_path, 'w') as submission_metadata_file:
                json.dump({}, submission_metadata_file)

        with open(submission_metadata_path, 'r') as submission_metadata_file:
            submission_metadata = json.load(submission_metadata_file)

        with open(submission_metadata_path, 'w') as submission_metadata_file:
            json.dump(submission_metadata, submission_metadata_file)

        log.info('Initialized LOCAL  Repo: %r' % (repo.working_tree_dir,))
        log.info('Initialized REMOTE Repo: %r' % (project.web_url,))

        return repo, project

    def get_repository(self, submission):
        submission_path = submission.get_absolute_path()
        submission_git_path = os.path.join(submission_path, '.git')

        if os.path.exists(submission_git_path):
            repo = git.Repo(submission_path)
        else:
            repo = None

        return repo


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    SubmissionManager(app)
