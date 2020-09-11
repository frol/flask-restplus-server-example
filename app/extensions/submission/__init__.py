# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""
Submission Management.

"""
import logging

from flask import current_app, request, session, render_template  # NOQA
from flask_login import current_user  # NOQA
import gitlab
import git  # NOQA

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

            self.namespace = namespace
            log.info('Using namespace: %r' % (self.namespace,))

            self.initialized = True

    def init_repository(self, submission, remote=True):
        if remote:
            self.ensure_initialed()

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
            remote_url = project.web_url
        else:
            remote_url = None

        # Initialize local repo
        print(remote_url)

        import utool as ut

        ut.embed()


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    SubmissionManager(app)
