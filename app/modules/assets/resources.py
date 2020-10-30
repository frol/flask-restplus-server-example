# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation
"""
RESTful API Assets resources
--------------------------
"""

import logging

from flask_restplus_patched import Resource
from flask_restplus._http import HTTPStatus
from app.extensions.api import Namespace
from app.modules.users import permissions
from app.extensions.api.parameters import PaginationParameters

from .models import Asset

from . import schemas


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('assets', description='Assets')  # pylint: disable=invalid-name


@api.route('/')
@api.login_required(oauth_scopes=['assets:read'])
class Assets(Resource):
    """
    Manipulations with Assets.
    """

    @api.login_required(oauth_scopes=['assets:read'])
    @api.permission_required(permissions.AdminRolePermission())
    @api.response(schemas.BaseAssetSchema(many=True))
    @api.parameters(PaginationParameters())
    def get(self, args):
        """
        List of Assets.

        Returns a list of Asset starting from ``offset`` limited by ``limit``
        parameter.
        """
        return Asset.query.offset(args['offset']).limit(args['limit'])


@api.route('/<uuid:asset_guid>')
@api.login_required(oauth_scopes=['assets:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND,
    description='Asset not found.',
)
@api.resolve_object_by_model(Asset, 'asset')
class AssetByID(Resource):
    """
    Manipulations with a specific Asset.
    """

    @api.permission_required(permissions.AdminRolePermission())
    @api.response(schemas.DetailedAssetSchema())
    def get(self, asset):
        """
        Get Asset details by ID.
        """
        return asset

    # @api.login_required(oauth_scopes=['assets:write'])
    # @api.permission_required(permissions.WriteAccessPermission())
    # @api.response(code=HTTPStatus.CONFLICT)
    # @api.response(code=HTTPStatus.NO_CONTENT)
    # def delete(self, asset):
    #     """
    #     Delete a Asset by ID.
    #     """
    #     import utool as ut
    #     ut.embed()
    #     context = api.commit_or_abort(
    #         db.session,
    #         default_error_message="Failed to delete the Asset."
    #     )
    #     with context:
    #         db.session.delete(asset)
    #     return None
