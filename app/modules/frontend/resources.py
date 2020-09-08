# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation
"""
RESTful API Frontends resources
--------------------------
"""

import logging
import glob
import os

from flask import current_app
from flask_login import current_user  # NOQA
from flask_restplus_patched import Resource

from app.extensions.api import Namespace

import datetime
import pytz


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('frontends', description='Frontends')  # pylint: disable=invalid-name


DATETIME_FMTSTR = '%Y%m%d-%H%M%S'
PST = pytz.timezone('US/Pacific')


def parse_frontend_versions():
    static_root = current_app.config.get('STATIC_ROOT')
    frontend_dist_list = glob.glob(os.path.join(static_root, 'dist-*/'))
    frontend_dist_latest = glob.glob(os.path.join(static_root, 'dist-latest/'))

    assert len(frontend_dist_latest) == 1
    frontend_dist_latest = frontend_dist_latest[0]
    assert frontend_dist_latest in frontend_dist_list
    frontend_dist_list.remove(frontend_dist_latest)

    frontend_link_latest = os.path.realpath(frontend_dist_latest)
    frontend_link_latest = os.path.join(frontend_link_latest, '')
    assert frontend_link_latest in frontend_dist_list

    frontend_versions = {}
    for frontend_dist in frontend_dist_list:
        frontend_dist_ = frontend_dist.split('-')
        frontend_version = frontend_dist_[1]
        frontend_timestamp = frontend_dist_[2:]

        frontend_active = frontend_dist == frontend_link_latest

        try:
            frontend_timestamp = '-'.join(frontend_timestamp)
            frontend_timestamp = frontend_timestamp.strip('/')
            frontend_timestamp = frontend_timestamp[:-3]
            frontend_datetime = datetime.datetime.strptime(
                frontend_timestamp, DATETIME_FMTSTR
            )
            frontend_datetime = frontend_datetime.replace(tzinfo=PST)
            frontend_time = frontend_datetime.strftime('%B %d, %Y, %H:%M:%S %p Pacific')
        except Exception:
            frontend_time = 'Parse Error: %r' % (frontend_timestamp,)

        frontend_versions[frontend_version] = {
            'built': frontend_time,
            'active': frontend_active,
        }

    return frontend_versions


@api.route('/')
@api.login_required(oauth_scopes=['frontends:read'])
class Frontends(Resource):
    """
    Manipulations with Frontends.
    """

    def get(self):
        """
        List of frontend versions.
        """
        response = parse_frontend_versions()
        return response
