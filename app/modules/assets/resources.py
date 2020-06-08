# -*- coding: utf-8 -*-
# pylint: disable=bad-continuation
"""
RESTful API Assets resources
--------------------------
"""

import logging

from flask import request, current_app
from flask_restplus_patched import Resource
from flask_restplus._http import HTTPStatus
from werkzeug.utils import secure_filename

from app.extensions import db
from app.extensions.api import Namespace, abort
from app.modules.users import permissions
from app.extensions.api.parameters import PaginationParameters

from app.modules.auth.models import Code

from .models import Asset

from . import schemas

from PIL import Image
import os


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('assets', description='Assets')  # pylint: disable=invalid-name


def process_file_upload(square=False):
    FINAL_EXT = '.jpg'

    asset_path = current_app.config.get('ASSET_DATABASE_PATH', None)
    assert asset_path is not None
    assert os.path.exists(asset_path)

    allowed_extensions = current_app.config.get('ASSET_ALLOWED_EXTS', [])

    upload_file = request.files.get('file', None)
    if upload_file is None:
        abort(code=HTTPStatus.CONFLICT, message='The file was not uploaded as expected')

    upload_filename = upload_file.filename
    upload_ext = os.path.splitext(upload_filename)[1]
    if upload_ext not in allowed_extensions:
        abort(code=HTTPStatus.CONFLICT, message="The file's extension is not supported")

    while True:
        asset_code = Code.generate(64)
        asset_filename = '%s.original%s' % (asset_code, upload_ext)

        # Sanity check
        asset_filename = secure_filename(asset_filename)
        asset_filepath = os.path.join(asset_path, asset_filename,)

        final_asset_filepath = '%s%s' % (asset_code, FINAL_EXT,)
        final_asset_filepath = os.path.join(asset_path, final_asset_filepath,)

        # Check if we have a database asset with that code (very unlikely)
        existing_asset = Asset.query.filter_by(code=asset_code).first()
        flag_list = [
            os.path.exists(asset_filepath),
            os.path.exists(final_asset_filepath),
            existing_asset is not None,
        ]

        if True not in flag_list:
            break

    # Save original file to disk
    upload_file.save(asset_filepath)

    # Load image (checking for compatibility and security issues)
    asset = Image.open(asset_filepath)

    # Strip all EXIF
    asset_data = list(asset.getdata())
    asset_ = Image.new(asset.mode, asset.size)
    asset_.putdata(asset_data)

    # Save all assets as JPGs with high optimization to reduce storage
    asset_.thumbnail((1000, 1000), Image.ANTIALIAS)

    if square:
        width, height = asset_.size  # Get dimensions
        value = min(width, height)
        left = (width - value) / 2
        top = (height - value) / 2
        right = (width + value) / 2
        bottom = (height + value) / 2
        asset_ = asset_.crop((left, top, right, bottom))

    # Optimize JPEG file and save
    asset_.save(final_asset_filepath, quality=75, optimize=True)
    log.info('Saved asset: %r' % (asset_code,))

    # Remove the original upload now that we have an optimized version saved to disk
    os.remove(asset_filepath)

    context = api.commit_or_abort(
        db.session, default_error_message='Failed to create a new asset.'
    )
    with context:
        asset_kwargs = {
            'code': asset_code,
            'ext': FINAL_EXT,
        }
        new_asset = Asset(**asset_kwargs)
        db.session.add(new_asset)
    db.session.refresh(new_asset)

    return new_asset


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

    @api.login_required(oauth_scopes=['assets:write'])
    @api.permission_required(permissions.AdminRolePermission())
    @api.response(schemas.DetailedAssetSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def post(self):
        """
        Create a new instance of Asset.
        """
        return process_file_upload()


@api.route('/<int:asset_id>')
@api.login_required(oauth_scopes=['assets:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND, description='Asset not found.',
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
