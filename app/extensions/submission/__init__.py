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
    def __init__(self, app, pre_initialize=True, *args, **kwargs):
        super(SubmissionManager, self).__init__(*args, **kwargs)
        self.initialized = False

        self.app = app
        app.sub = self

        self.gl = None

        if pre_initialize:
            self.ensure_initialed()

    def ensure_initialed(self):
        if not self.initialized:
            assert self.gl is None
            logging.info('Logging into Submission GitLab...')
            remote_uri = self.app.config.get('GITLAB_REMOTE_URI', None)
            remote_personal_access_token = self.app.config.get(
                'GITLAB_REMOTE_LOGIN_PAT', None
            )

            self.gl = gitlab.Gitlab(
                remote_uri, private_token=remote_personal_access_token
            )
            self.gl.auth()
            logging.info('Logged in: %r' % (self.gl,))


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    SubmissionManager(app)
