# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""
Ecological Data Management (EDM) manager.

"""
import logging

from flask import current_app, request, session, render_template  # NOQA
from flask_login import current_user  # NOQA
from app.extensions import db
import requests
from collections import namedtuple
import types
import json

import pytz

import keyword
import uuid


KEYWORD_SET = set(keyword.kwlist)


log = logging.getLogger(__name__)

PST = pytz.timezone('US/Pacific')


def _json_object_hook(data):
    keys = list(data.keys())
    keys_set = set(keys)
    keys_ = []
    for key in keys:
        if key in KEYWORD_SET:
            key_ = '%s_' % (key,)
            assert key_ not in keys_set
        else:
            key_ = key
        keys_.append(key_)
    values = data.values()
    data_ = namedtuple('obj', keys_)(*values)
    return data_


class EDMManagerEndpointMixin(object):

    ENDPOINT_PREFIX = 'api'

    # We use // as a shorthand for prefix
    # fmt: off
    ENDPOINTS = {
        'session': {
            'login': '//v0/login?content={"login":"%s","password":"%s"}',
        },
        'user': {
            'list': '//v0/org.ecocean.User/list',
            'data': '//v0/org.ecocean.User/%s',
        },
        'encounter': {
            'list': '//v0/org.ecocean.Encounter/list',
        },
        'organization': {
            'list': '//v0/org.ecocean.Organization/list',
            'data': '//v0/org.ecocean.Organization/%s',
        },
        'collaboration': {
            'list': '//v0/org.ecocean.security.Collaboration/list',
        },
        'role': {
            'list': '//v0/org.ecocean.Role/list',
        },
    }
    # fmt: on

    def _endpoint_fmtstr(self, tag, target='default'):
        endpoint_url = self.uris[target]
        endpoint_tag_fmtstr = self._endpoint_tag_fmtstr(tag)
        assert endpoint_tag_fmtstr is not None, 'The endpoint tag was not recognized'

        if endpoint_tag_fmtstr.startswith('//'):
            endpoint_tag_fmtstr = endpoint_tag_fmtstr[2:]
            endpoint_tag_fmtstr = '%s/%s' % (self.ENDPOINT_PREFIX, endpoint_tag_fmtstr,)

        endpoint_url_ = endpoint_url.strip('/')
        endpoint_fmtstr = '%s/%s' % (endpoint_url_, endpoint_tag_fmtstr,)
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


class EDMManagerUserMixin(object):
    def get_users(self, target='default'):
        response = self._get('user.list', target=target)

        users = {}
        for value in response:
            try:
                guid = value.id
                version = value.version
            except AttributeError as exception:
                log.error('Invalid response from EDM [user.list]')
                raise exception

            guid = uuid.UUID(guid)
            assert isinstance(version, int)

            users[guid] = {'version': version}

        return users

    def get_user_data(self, guid, target='default'):
        assert isinstance(guid, uuid.UUID)
        response = self._get('user.data', guid, target=target)
        return response


class EDMManagerEncounterMixin(object):
    def get_encounters(self, target='default'):
        response = self._get('encounters.list', target=target)
        return response


class EDMManager(EDMManagerEndpointMixin, EDMManagerUserMixin):
    # pylint: disable=abstract-method
    """
        note the content of User in the 2nd item has stuff you can ignore. it also has the id as "uuid" (which is what it is internally, sigh).  also note it references Organizations !  we didnt touch on this on the call, but i think this should (must?) live with Users.  what we have in java is very lightweight anyway, so no loss to go away.   as you can see, user.organizations is an array of orgs, and (since it is many-to-many) you will see org.members is a list of Users.  easy peasy.  btw, by the time we got to Organizations, we did call the primary key id and make it a uuid.  "live and learn".  :confused:
    also!  the user.profileAsset is fabricated!  ben wanted something so i literally hardcoded a random choice (including empty) from a list of like 4 user faces. haha.  so you arent going crazy if you see this change per user.  and obviously in the future the contents of this will be more whatever we land on for final asset format.

        btw, as a bonus.  here is what an Organization is on wildbook[edm] ... they are hierarchical -- which i would argue we drop!!  it was fun for playing with, but i do not want to have to support that when security starts using these!!!  (no real world orgs use this currently anyway, not in any important way.)   other than that (and killing it off!) there are .members and .logoAsset.  boringly simple.
    https://nextgen.dev-wildbook.org/api/org.ecocean.Organization?id==%273b868b21-729f-46ca-933f-c4ecdf02e97d%27
    """

    def __init__(self, app, pre_initialize=False, *args, **kwargs):
        super(EDMManager, self).__init__(*args, **kwargs)
        self.initialized = False
        self.app = app
        app.edm = self

        if pre_initialize:
            self._ensure_initialed()

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
            print('Invalid keys %r provided in EDM_URIS' % (invalid_key_list,))
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

            message = 'EDM Authentication for %s unspecified (username)' % (target,)
            assert username is not None, message
            message = 'EDM Authentication for %s unspecified (password)' % (target,)
            assert password is not None, message

            self.sessions[target] = requests.Session()
            self._get('session.login', username, password, target=target)

    def _ensure_initialed(self):
        if not self.initialized:
            self.initialized = True
            self._parse_config_edm_uris(self.app)
            self._init_sessions(self.app)

    def _get(
        self,
        tag,
        *args,
        target='default',
        decode_as_object=True,
        decode_as_dict=False,
        verbose=True
    ):
        self._ensure_initialed()

        endpoint_fmtstr = self._endpoint_fmtstr(tag, target=target)
        endpoint = endpoint_fmtstr % args

        endpoint_encoded = requests.utils.quote(endpoint, safe='/?:=')

        if verbose:
            log.info('Sending request to: %r' % (endpoint_encoded,))

        with self.sessions[target] as target_session:
            response = target_session.get(endpoint_encoded)

        if response.ok:
            if decode_as_object and decode_as_dict:
                log.warning(
                    'Both decode_object and decode_dict are True, defaulting to object'
                )
                decode_as_dict = False

            if decode_as_object:
                response = json.loads(response.text, object_hook=_json_object_hook)

            if decode_as_dict:
                response = response.json()

        return response


class EDMObjectMixin(object):
    def _process_edm_attribute(self, data, edm_attribute):
        edm_attribute = edm_attribute.strip()
        edm_attribute = edm_attribute.strip('.')
        edm_attribute_list = edm_attribute.split('.')

        num_components = len(edm_attribute_list)

        if num_components == 0:
            raise AttributeError()

        edm_attribute_ = edm_attribute_list[0]
        edm_attribute_ = edm_attribute_.strip()
        data_ = getattr(data, edm_attribute_)

        if num_components == 1:
            return data_

        edm_attribute_list_ = edm_attribute_list[1:]
        edm_attribute_ = '.'.join(edm_attribute_list_)

        return self._process_edm_attribute(data_, edm_attribute_)

    def _process_edm_data(self, data, version):
        with db.session.begin():
            for edm_attribute in self.EDM_ATTRIBUTE_MAPPING:
                try:
                    edm_value = self._process_edm_attribute(data, edm_attribute)

                    attribute = self.EDM_ATTRIBUTE_MAPPING.get(edm_attribute, None)
                    assert attribute is not None
                    assert hasattr(self, attribute), 'User attribute not found'

                    attribute_ = getattr(self, attribute)

                    if isinstance(attribute_, (types.MethodType,)):
                        attribute_(edm_value)
                    else:
                        setattr(self, attribute, edm_value)
                except AttributeError:
                    log.warning('Could not find EDM attribute %r' % (edm_attribute,))

            self.version = version
            db.session.merge(self)


def init_app(app, **kwargs):
    # pylint: disable=unused-argument
    """
    API extension initialization point.
    """
    EDMManager(app)
