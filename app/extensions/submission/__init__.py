# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""
Submission Management.

"""
import logging

from flask import current_app, request, session, render_template  # NOQA
from flask_login import current_user  # NOQA

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

        if pre_initialize:
            self.ensure_initialed()

    def ensure_initialed(self):
        remote_uri = self.app.config.get('GIT_REMOTE_URI', None)
        remote_personal_access_token = self.app.config.get('GIT_REMOTE_LOGIN_PAT', None)

        print(remote_uri, remote_personal_access_token)


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    SubmissionManager(app)
