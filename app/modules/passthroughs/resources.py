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


@edm_pass.route('/<string:target>/', defaults={'path': None})
@edm_pass.route('/<string:target>/<path:path>')
@edm_pass.login_required(oauth_scopes=['passthroughs:read'])
class EDMPassthroughs(Resource):
    def get(self, target, path):
        """
        List the possible EDM passthrough targets.
        """
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

        params = {}
        params.update(request.args)
        params.update(request.form)

        response = current_app.edm.get_passthrough(
            None,
            endpoint=endpoint,
            target=target,
            decode_as_object=False,
            decode_as_dict=False,
            passthrough_kwargs={'params': params},
        )
        return response
