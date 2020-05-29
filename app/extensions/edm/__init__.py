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

    ENDPOINT_PREFIX = 'api/v0'

    # We use // as a shorthand for prefix
    ENDPOINTS = {
        'session': {
            'login': '//login?content={"login":"%s","password":"%s"}',
        },
        'user' : {
            'list': '//org.ecocean.User/list',
        },
        'encounter' : {
            'list': '//org.ecocean.Encounter/list',
        },
    }

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
        self.sessions = {}
        for target in self.uris:
            auth = self.auths[target]

            username = auth.get('username', auth.get('user', None))
            password = auth.get('password', auth.get('pass', None))

            message = 'EDM Authentication for %s unspecified (username)' % (target, )
            assert username is not None, message
            message = 'EDM Authentication for %s unspecified (password)' % (target, )
            assert password is not None, message

            self.sessions[target] = requests.Session()
            self._get('session.login', username, password, target=target)

    def _endpoint_fmtstr(self, tag, target='default'):
        endpoint_url = self.uris[target]
        endpoint_tag_fmtstr = self._endpoint_tag_fmtstr(tag)
        assert endpoint_tag_fmtstr is not None, 'The endpoint tag was not recognized'

        if endpoint_tag_fmtstr.startswith('//'):
            endpoint_tag_fmtstr = endpoint_tag_fmtstr[2:]
            endpoint_tag_fmtstr = '%s/%s' % (self.ENDPOINT_PREFIX, endpoint_tag_fmtstr, )

        endpoint_url_ = endpoint_url.strip('/')
        endpoint_fmtstr = '%s/%s' % (endpoint_url_, endpoint_tag_fmtstr, )
        return endpoint_fmtstr

    def _endpoint_tag_fmtstr(self, tag):
        endpoint = self.ENDPOINTS

        component_list = tag.split('.')
        for comoponent in component_list:
            try:
                endpoint_ = endpoint.get(comoponent, None)
            except Exception:
                endpoint_ = None

            if endpoint_ is None:
                break

            endpoint = endpoint_

        return endpoint

    def _get(self, tag, *args, target='default', json=True):
        endpoint_fmtstr = self._endpoint_fmtstr(tag, target=target)
        endpoint = endpoint_fmtstr % args

        endpoint_encoded = requests.utils.quote(endpoint, safe="/?:=")

        with self.sessions[target] as target_session:
            response = target_session.get(endpoint_encoded)

        if response.ok and json:
            response = response.json()

        return response

    def get_users(self, target='default'):
        response = self._get('user.list', target=target)
        return response

    def get_encounters(self, target='default'):
        response = self._get('user.list', target=target)
        return response


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    EDMManager(app)
