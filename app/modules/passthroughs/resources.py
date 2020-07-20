# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation
"""
RESTful API Passthroughs resources
--------------------------
"""

import logging

from flask_restplus_patched import Resource
from flask_restplus._http import HTTPStatus

from app.extensions import db
from app.extensions.api import Namespace
from app.extensions.api.parameters import PaginationParameters
from app.modules.users import permissions


from . import parameters, schemas


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
edm_pass = Namespace(
    'passthroughs/edm', description='EDM Passthroughs'
)  # pylint: disable=invalid-name
acm_pass = Namespace(
    'passthroughs/acm', description='ACM Passthroughs'
)  # pylint: disable=invalid-name


@edm_pass.route('/')
@edm_pass.login_required(oauth_scopes=['passthroughs:read'])
class EDMPassthroughs(Resource):
    """
    Manipulations with Passthroughs.
    """

    @edm_pass.parameters(PaginationParameters())
    @edm_pass.response(schemas.BasePassthroughSchema(many=True))
    def get(self, args):
        """
        List of Passthrough.

        Returns a list of Passthrough starting from ``offset`` limited by ``limit``
        parameter.
        """
        import utool as ut

        ut.embed()
        return None

    @edm_pass.login_required(oauth_scopes=['passthroughs:write'])
    @edm_pass.parameters(parameters.CreatePassthroughParameters())
    @edm_pass.response(schemas.BasePassthroughSchema())
    @edm_pass.response(code=HTTPStatus.CONFLICT)
    def post(self, args):
        """
        Create a new instance of Passthrough.
        """
        return None
