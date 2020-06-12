# encoding: utf-8
# pylint: disable=bad-continuation
"""
RESTful API Encounters resources
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
from .models import Encounter


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('encounters', description="Encounters")  # pylint: disable=invalid-name


@api.route('/')
@api.login_required(oauth_scopes=['encounters:read'])
class Encounters(Resource):
    """
    Manipulations with Encounters.
    """

    @api.parameters(PaginationParameters())
    @api.response(schemas.BaseEncounterSchema(many=True))
    def get(self, args):
        """
        List of Encounter.

        Returns a list of Encounter starting from ``offset`` limited by ``limit``
        parameter.
        """
        return Encounter.query.offset(args['offset']).limit(args['limit'])

    @api.login_required(oauth_scopes=['encounters:write'])
    @api.parameters(parameters.CreateEncounterParameters())
    @api.response(schemas.DetailedEncounterSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def post(self, args):
        """
        Create a new instance of Encounter.
        """
        context = api.commit_or_abort(
            db.session,
            default_error_message="Failed to create a new Encounter"
        )
        with context:
            encounter = Encounter(**args)
            db.session.add(encounter)
        return encounter


@api.route('/<uuid:encounter_guid>')
@api.login_required(oauth_scopes=['encounters:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND,
    description="Encounter not found.",
)
@api.resolve_object_by_model(Encounter, 'encounter')
class EncounterByID(Resource):
    """
    Manipulations with a specific Encounter.
    """

    @api.response(schemas.DetailedEncounterSchema())
    def get(self, encounter):
        """
        Get Encounter details by ID.
        """
        return encounter

    @api.login_required(oauth_scopes=['encounters:write'])
    @api.permission_required(permissions.WriteAccessPermission())
    @api.parameters(parameters.PatchEncounterDetailsParameters())
    @api.response(schemas.DetailedEncounterSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def patch(self, args, encounter):
        """
        Patch Encounter details by ID.
        """
        context = api.commit_or_abort(
            db.session,
            default_error_message="Failed to update Encounter details."
        )
        with context:
            parameters.PatchEncounterDetailsParameters.perform_patch(args, obj=encounter)
            db.session.merge(encounter)
        return encounter

    @api.login_required(oauth_scopes=['encounters:write'])
    @api.permission_required(permissions.WriteAccessPermission())
    @api.response(code=HTTPStatus.CONFLICT)
    @api.response(code=HTTPStatus.NO_CONTENT)
    def delete(self, encounter):
        """
        Delete a Encounter by ID.
        """
        context = api.commit_or_abort(
            db.session,
            default_error_message="Failed to delete the Encounter."
        )
        with context:
            db.session.delete(encounter)
        return None
