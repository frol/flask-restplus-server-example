# encoding: utf-8
# pylint: disable=bad-continuation
"""
RESTful API Redemptions resources
--------------------------
"""

import logging

from flask import current_app  # NOQA
from flask_login import current_user  # NOQA
from flask_restplus_patched import Resource
import utool as ut

from app.extensions.api import Namespace

from app.modules.users import permissions


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('dev', description="Developer Tools")  # pylint: disable=invalid-name


@api.route('/embed/')
class Develop(Resource):

    @api.login_required(oauth_scopes=['users:read'])
    @api.permission_required(permissions.AdminRolePermission())
    def get(self):
        '''
        from app.modules.auth.models import Codes
        '''
        ut.embed()
        return True
