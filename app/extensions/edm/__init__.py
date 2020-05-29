# encoding: utf-8
# pylint: disable=no-self-use
"""
Ecological Data Management (EDM) manager.

"""
import logging

from flask import current_app, request, session, render_template  # NOQA
from flask_login import current_user  # NOQA

import re

import datetime
import pytz


log = logging.getLogger(__name__)

PST = pytz.timezone('US/Pacific')


class EDMManager(object):
    # pylint: disable=abstract-method
    """
    A project-specific implementation of OAuth2RequestValidator, which connects
    our User and OAuth2* implementations together.
    """

    def __init__(self, app, *args, **kwargs):
        self._parse_config_edm_uris(app)

        super(EDMManager, self).__init__(*args, **kwargs)
        app.edm = self

    def _parse_config_edm_uris(self, app):
        edm_uri_dict = app.config.get('EDM_URIS', None)

        try:
            key_list = []
            invalid_key_list = []

            edm_uri_key_list = sorted(edm_uri_dict.keys())
            for key in edm_uri_key_list:
                valid = True

                try:
                    if not isinstance(key, int):
                        # key isn't an integer or a parsable integer
                        try:
                            key_ = int(key)
                            key = key_
                        except Exception:
                            valid = False

                    if key < 0:
                        # key is negative
                        valid = False

                    if key in key_list + invalid_key_list:
                        # key seen before, no duplicates allowed
                        valid = False

                    if key >= len(edm_uri_key_list):
                        # key order is higher than the total, no skips allowed
                        valid = False

                except Exception:
                    valid = False

                if valid:
                    key_list.append(key)
                else:
                    invalid_key_list.append(key)

            if len(invalid_key_list) > 0:
                raise ValueError('Invalid keys provided')

        except Exception as exception:
            print('Invalid keys %r provided in EDM_URIS' % (invalid_key_list, ))
            raise exception

        key_list = sorted(key_list)

        assert 0 in key_list, 'EDM_URIS must contain an integer key 0'
        assert len(key_list) == len(set(key_list)), 'EDM_URIS cannot contain duplicates'
        assert key_list[0] == 0, 'EDM_URIS is mis-configured'
        assert key_list[-1] == len(key_list) - 1, 'EDM_URIS is mis-configured'

        uris = {}
        for key in key_list:
            if key == 0:
                uris['default'] = edm_uri_dict[key]
            uris[key] = edm_uri_dict[key]

        self.uris = uris

    def get_users_list(self, target='default'):
        'https://nextgen.dev-wildbook.org/api/v0/org.ecocean.User/list'


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    EDMManager(app)
