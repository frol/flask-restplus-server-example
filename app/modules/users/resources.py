# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods
"""
RESTful API User resources
--------------------------
"""

import logging
import datetime  # NOQA
import pytz

from sqlalchemy import or_, and_

from flask import current_app  # NOQA
from flask_login import current_user
from flask_restplus_patched import Resource
from flask_restplus._http import HTTPStatus
from app.extensions.api import abort

from app.extensions.api import Namespace

from . import permissions, schemas, parameters
from .models import db, User

from app.modules.auth.models import Code, CodeTypes
from app.modules.assets.resources import process_file_upload


log = logging.getLogger(__name__)
api = Namespace('users', description='Users')


PST = pytz.timezone('US/Pacific')


@api.route('/')
class Users(Resource):
    """
    Manipulations with users.
    """

    @api.login_required(oauth_scopes=['users:read'])
    @api.permission_required(permissions.StaffRolePermission())
    @api.response(schemas.BaseUserSchema(many=True))
    @api.paginate(parameters.ListUserParameters())
    def get(self, args):
        """
        List of users.

        Returns a list of users starting from ``offset`` limited by ``limit``
        parameter.
        """
        search = args.get('search', None)
        if search is not None and len(search) == 0:
            search = None

        if search is not None:
            search = search.strip().split(' ')
            search = [term.strip() for term in search]
            search = [term for term in search if len(term) > 0]

            or_terms = []
            for term in search:
                codes = (
                    Code.query.filter_by(code_type=CodeTypes.checkin)
                    .filter(Code.accept_code.contains(term),)
                    .all()
                )
                code_users = set([])
                for code in codes:
                    if not code.is_expired:
                        code_users.add(code.user.guid)

                or_term = or_(
                    User.guid.in_(code_users),
                    User.email.contains(term),
                    User.affiliation.contains(term),
                    User.forum_id.contains(term),
                    User.full_name.contains(term),
                )
                or_terms.append(or_term)
            users = User.query.filter(and_(*or_terms))
        else:
            users = User.query

        return users.order_by(User.guid)

    @api.parameters(parameters.CreateUserParameters())
    @api.response(schemas.DetailedUserSchema())
    @api.response(code=HTTPStatus.FORBIDDEN)
    @api.response(code=HTTPStatus.CONFLICT)
    @api.doc(id='create_user')
    def post(self, args):
        """
        Create a new user.
        """
        from app.modules.auth.models import _generate_salt

        email = args.get('email', None)
        user = User.query.filter_by(email=email).first()

        if user is not None:
            abort(
                code=HTTPStatus.CONFLICT, message='The email address is already in use.'
            )

        if 'password' not in args:
            args['password'] = _generate_salt(128)

        args['is_active'] = True

        context = api.commit_or_abort(
            db.session, default_error_message='Failed to create a new user.'
        )
        with context:
            new_user = User(**args)
            db.session.add(new_user)
        db.session.refresh(new_user)

        return new_user

    @api.login_required(oauth_scopes=['users:write'])
    @api.permission_required(permissions.AdminRolePermission())
    @api.parameters(parameters.DeleteUserParameters())
    def delete(self, args):
        """
        Remove a member.
        """
        context = api.commit_or_abort(
            db.session, default_error_message='Failed to delete user.'
        )
        with context:
            user_guid = args['user_guid']
            user = User.query.filter_by(id=user_guid).first_or_404()
            db.session.delete(user)

        return None


@api.route('/<uuid:user_guid>')
@api.login_required(oauth_scopes=['users:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND, description='User not found.',
)
@api.resolve_object_by_model(User, 'user')
class UserByID(Resource):
    """
    Manipulations with a specific user.
    """

    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['user']},
    )
    @api.response(schemas.DetailedUserSchema())
    def get(self, user):
        """
        Get user details by ID.
        """
        return user

    @api.login_required(oauth_scopes=['users:write'])
    @api.permission_required(
        permissions.OwnerModifyRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['user']},
    )
    @api.permission_required(permissions.WriteAccessPermission())
    @api.parameters(parameters.PatchUserDetailsParameters())
    @api.response(schemas.DetailedUserSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def patch(self, args, user):
        """
        Patch user details by ID.
        """
        context = api.commit_or_abort(
            db.session, default_error_message='Failed to update user details.'
        )
        with context:
            parameters.PatchUserDetailsParameters.perform_patch(args, user)
            db.session.merge(user)
        db.session.refresh(user)

        return user


@api.route('/picture/<uuid:user_guid>')
@api.login_required(oauth_scopes=['assets:read', 'users:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND, description='User not found.',
)
@api.resolve_object_by_model(User, 'user')
class UserArtworkByID(Resource):
    """
    Manipulations with a specific User.
    """

    @api.login_required(oauth_scopes=['assets:write', 'users:write'])
    @api.permission_required(
        permissions.OwnerModifyRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['user']},
    )
    @api.permission_required(permissions.WriteAccessPermission())
    @api.response(schemas.DetailedUserSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def post(self, user):
        """
        Create a new instance of Asset.
        """
        asset = process_file_upload(square=True)
        context = api.commit_or_abort(
            db.session, default_error_message='Failed to update User details.'
        )
        with context:
            user.profile_asset_guid = asset.guid
            db.session.merge(user)

        return user


@api.route('/me')
@api.login_required(oauth_scopes=['users:read'])
class UserMe(Resource):
    """
    Useful reference to the authenticated user itself.
    """

    @api.response(schemas.PersonalUserSchema())
    def get(self):
        """
        Get current user details.
        """
        return User.query.get_or_404(current_user.guid)


@api.route('/edm/sync')
# @api.login_required(oauth_scopes=['users:read'])
class UserEDMSync(Resource):
    """
    Useful reference to the authenticated user itself.
    """

    # @api.response(schemas.DetailedUserSchema())
    def get(self, refresh=False):
        """
        Get current user details.
        """
        edm_users, new_users, updated_users, failed_users = User.edm_sync_users(
            refresh=refresh
        )

        response = {
            'local': User.query.count(),
            'remote': len(edm_users),
            'added': len(new_users),
            'updated': len(updated_users),
            'failed': len(failed_users),
        }

        return response
