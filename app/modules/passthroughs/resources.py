# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation
"""
RESTful API Passthroughs resources
--------------------------
"""

import logging

from flask import current_app, request
from flask_restplus_patched import Resource
from app.extensions.api import Namespace

from werkzeug.exceptions import BadRequest

import json


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
edm_pass = Namespace(
    'passthroughs/edm', description='EDM Passthroughs'
)  # pylint: disable=invalid-name
acm_pass = Namespace(
    'passthroughs/acm', description='ACM Passthroughs'
)  # pylint: disable=invalid-name


@edm_pass.route('/')
@edm_pass.login_required(oauth_scopes=['passthroughs:read'])
class EDMPassthroughTargets(Resource):
    """
    Manipulations with Passthroughs.
    """

    def get(self):
        """
        List the possible EDM passthrough targets.
        """
        current_app.edm.ensure_initialed()
        targets = list(current_app.edm.targets)
        return targets


def _request_passthrough(target, path, request_func, passthrough_kwargs):
    try:
        # Try to convert string integers to integers
        target = int(target)
    except ValueError:
        pass

    # Check target
    current_app.edm.ensure_initialed()
    targets = list(current_app.edm.targets)
    if target not in targets:
        raise BadRequest('The specified target %r is invalid.' % (target,))

    endpoint_url_ = current_app.edm.get_target_endpoint_url(target)
    endpoint = '%s/%s' % (endpoint_url_, path,)

    headers = passthrough_kwargs.get('headers', {})
    allowed_header_key_list = [
        'Accept',
        'Content-Type',
        'User-Agent',
    ]
    for header_key in allowed_header_key_list:
        header_value = request.headers.get(header_key, None)
        header_existing = headers.get(header_key, None)
        if header_value is not None and header_existing is None:
            headers[header_key] = header_value
    passthrough_kwargs['headers'] = headers

    response = request_func(
        None,
        endpoint=endpoint,
        target=target,
        decode_as_object=False,
        decode_as_dict=False,
        passthrough_kwargs=passthrough_kwargs,
    )
    return response


@edm_pass.route('/<string:target>/', defaults={'path': None})
@edm_pass.route('/<string:target>/<path:path>')
@edm_pass.login_required(oauth_scopes=['passthroughs:read'])
class EDMPassthroughs(Resource):
    def get(self, target, path):
        """
        List the possible EDM passthrough targets.
        """
        params = {}
        params.update(request.args)
        params.update(request.form)

        request_func = current_app.edm.get_passthrough
        passthrough_kwargs = {'params': params}

        response = _request_passthrough(target, path, request_func, passthrough_kwargs)

        return response

    def post(self, target, path):
        """
        List the possible EDM passthrough targets.
        """
        data = {}
        data.update(request.args)
        data.update(request.form)
        try:
            data_ = json.loads(request.data)
            data.update(data_)
        except Exception:
            pass

        request_func = current_app.edm.post_passthrough
        passthrough_kwargs = {'json': data}

        files = request.files
        if len(files) > 0:
            passthrough_kwargs['files'] = files

        response = _request_passthrough(target, path, request_func, passthrough_kwargs)

        return response
