# encoding: utf-8
# pylint: disable=bad-continuation
"""
RESTful API Collaborations resources
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
from .models import Collaboration


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('collaborations', description="Collaborations")  # pylint: disable=invalid-name


@api.route('/')
@api.login_required(oauth_scopes=['collaborations:read'])
class Collaborations(Resource):
    """
    Manipulations with Collaborations.
    """

    @api.parameters(PaginationParameters())
    @api.response(schemas.BaseCollaborationSchema(many=True))
    def get(self, args):
        """
        List of Collaboration.

        Returns a list of Collaboration starting from ``offset`` limited by ``limit``
        parameter.
        """
        return Collaboration.query.offset(args['offset']).limit(args['limit'])

    @api.login_required(oauth_scopes=['collaborations:write'])
    @api.parameters(parameters.CreateCollaborationParameters())
    @api.response(schemas.DetailedCollaborationSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def post(self, args):
        """
        Create a new instance of Collaboration.
        """
        context = api.commit_or_abort(
            db.session,
            default_error_message="Failed to create a new Collaboration"
        )
        with context:
            collaboration = Collaboration(**args)
            db.session.add(collaboration)
        return collaboration


@api.route('/<uuid:collaboration_guid>')
@api.login_required(oauth_scopes=['collaborations:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND,
    description="Collaboration not found.",
)
@api.resolve_object_by_model(Collaboration, 'collaboration')
class CollaborationByID(Resource):
    """
    Manipulations with a specific Collaboration.
    """

    @api.response(schemas.DetailedCollaborationSchema())
    def get(self, collaboration):
        """
        Get Collaboration details by ID.
        """
        return collaboration

    @api.login_required(oauth_scopes=['collaborations:write'])
    @api.permission_required(permissions.WriteAccessPermission())
    @api.parameters(parameters.PatchCollaborationDetailsParameters())
    @api.response(schemas.DetailedCollaborationSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def patch(self, args, collaboration):
        """
        Patch Collaboration details by ID.
        """
        context = api.commit_or_abort(
            db.session,
            default_error_message="Failed to update Collaboration details."
        )
        with context:
            parameters.PatchCollaborationDetailsParameters.perform_patch(args, obj=collaboration)
            db.session.merge(collaboration)
        return collaboration

    @api.login_required(oauth_scopes=['collaborations:write'])
    @api.permission_required(permissions.WriteAccessPermission())
    @api.response(code=HTTPStatus.CONFLICT)
    @api.response(code=HTTPStatus.NO_CONTENT)
    def delete(self, collaboration):
        """
        Delete a Collaboration by ID.
        """
        context = api.commit_or_abort(
            db.session,
            default_error_message="Failed to delete the Collaboration."
        )
        with context:
            db.session.delete(collaboration)
        return None