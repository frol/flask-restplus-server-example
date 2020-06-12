# encoding: utf-8
# pylint: disable=bad-continuation
"""
RESTful API Organizations resources
--------------------------
"""

import logging

from flask_login import current_user
from flask_restplus_patched import Resource
from flask_restplus._http import HTTPStatus

from app.extensions import db
from app.extensions.api import Namespace
from app.extensions.api.parameters import PaginationParameters
from app.modules.users import permissions


from . import parameters, schemas
from .models import Organization


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('organizations', description="Organizations")  # pylint: disable=invalid-name


@api.route('/')
@api.login_required(oauth_scopes=['organizations:read'])
class Organizations(Resource):
    """
    Manipulations with Organizations.
    """

    @api.parameters(PaginationParameters())
    @api.response(schemas.BaseOrganizationSchema(many=True))
    def get(self, args):
        """
        List of Organization.

        Returns a list of Organization starting from ``offset`` limited by ``limit``
        parameter.
        """
        return Organization.query.offset(args['offset']).limit(args['limit'])

    @api.login_required(oauth_scopes=['organizations:write'])
    @api.parameters(parameters.CreateOrganizationParameters())
    @api.response(schemas.DetailedOrganizationSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def post(self, args):
        """
        Create a new instance of Organization.
        """
        context = api.commit_or_abort(
            db.session,
            default_error_message="Failed to create a new Organization"
        )
        with context:
            organization = Organization(**args)
            db.session.add(organization)
        return organization


@api.route('/<uuid:organization_guid>')
@api.login_required(oauth_scopes=['organizations:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND,
    description="Organization not found.",
)
@api.resolve_object_by_model(Organization, 'organization')
class OrganizationByID(Resource):
    """
    Manipulations with a specific Organization.
    """

    @api.response(schemas.DetailedOrganizationSchema())
    def get(self, organization):
        """
        Get Organization details by ID.
        """
        return organization

    @api.login_required(oauth_scopes=['organizations:write'])
    @api.permission_required(permissions.WriteAccessPermission())
    @api.parameters(parameters.PatchOrganizationDetailsParameters())
    @api.response(schemas.DetailedOrganizationSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def patch(self, args, organization):
        """
        Patch Organization details by ID.
        """
        context = api.commit_or_abort(
            db.session,
            default_error_message="Failed to update Organization details."
        )
        with context:
            parameters.PatchOrganizationDetailsParameters.perform_patch(args, obj=organization)
            db.session.merge(organization)
        return organization

    @api.login_required(oauth_scopes=['organizations:write'])
    @api.permission_required(permissions.WriteAccessPermission())
    @api.response(code=HTTPStatus.CONFLICT)
    @api.response(code=HTTPStatus.NO_CONTENT)
    def delete(self, organization):
        """
        Delete a Organization by ID.
        """
        context = api.commit_or_abort(
            db.session,
            default_error_message="Failed to delete the Organization."
        )
        with context:
            db.session.delete(organization)
        return None