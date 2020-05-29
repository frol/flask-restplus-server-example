# encoding: utf-8
# pylint: disable=no-self-use
"""
Ecological Data Management (EDM) manager.

"""
import logging

from flask import current_app, request, session, render_template  # NOQA
from flask_login import current_user  # NOQA
import requests

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
        self._init_sessions(app)

        super(EDMManager, self).__init__(*args, **kwargs)
        app.edm = self

    def _parse_config_edm_uris(self, app):
        edm_uri_dict = app.config.get('EDM_URIS', None)
        edm_authentication_dict = app.config.get('EDM_AUTHENTICATIONS', None)

        assert edm_uri_dict is not None, 'Must specify EDM_URIS in config'
        message = 'Must specify EDM_AUTHENTICATIONS in the secret config'
        assert edm_authentication_dict is not None, message

        try:
            key_list = []
            invalid_key_list = []

            edm_uri_key_list = sorted(edm_uri_dict.keys())
            edm_authentication_key_list = sorted(edm_authentication_dict.keys())

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

                    if key not in edm_authentication_key_list:
                        # Authentication not provided
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
        auths = {}
        for key in key_list:
            if key == 0:
                uris['default'] = edm_uri_dict[key]
                auths['default'] = edm_authentication_dict[key]
            uris[key] = edm_uri_dict[key]
            auths[key] = edm_authentication_dict[key]

        self.uris = uris
        self.auths = auths

    def _init_sessions(self, app):
        print(self.uris)
        print(self.auths)
        # import utool as ut
        # ut.embed()
        # self.sessions = {}
        # for target in self.uris:
        #     # create a session object
        #     s = requests.Session()

        #     # make a get request
        #     s.get('https://nextgen.dev-wildbook.org/api/v0/login?content=%7B%22login%22:%22test%22,%22password%22:%22test1234%22%7D')
        #     #s.get('https://nextgen.dev-wildbook.org/')

        #     # again make a get request
        #     r = s.get('https://nextgen.dev-wildbook.org/api/org.ecocean.User?uuid==%272eae47e3-94b3-44fd-a89c-af07d4d80e0c%27')

        #     # check if cookie is still set
        #     print(r.text)

    def get_users_list(self, target='default'):
        'https://nextgen.dev-wildbook.org/api/v0/org.ecocean.User/list'


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    EDMManager(app)
