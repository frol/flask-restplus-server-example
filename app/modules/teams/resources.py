# encoding: utf-8
"""
RESTful API Team resources
==========================
"""

import logging

from flask.ext.restplus import Resource
import sqlalchemy

from app.extensions import db
from app.extensions.api import api_v1, abort, http_exceptions
from app.extensions.api.parameters import PaginationParameters
from app.modules.users import permissions

from . import parameters, schemas
from .models import Team


log = logging.getLogger(__name__)
namespace = api_v1.namespace('teams', description="Teams")


@namespace.route('/')
class Teams(Resource):
    """
    Manipulations with teams.
    """

    @api_v1.login_required(scopes=['teams:read'])
    @api_v1.parameters(PaginationParameters())
    @api_v1.response(schemas.BaseTeamSchema(many=True))
    def get(self, args):
        """
        List of teams.

        Returns a list of teams starting from ``offset`` limited by ``limit``
        parameter.
        """
        return Team.query.all()[args['offset']: args['offset'] + args['limit']]

    @api_v1.login_required(scopes=['teams:write'])
    @api_v1.parameters(parameters.CreateTeamParameters())
    @api_v1.response(schemas.DetailedTeamSchema())
    @api_v1.response(code=http_exceptions.Conflict.code)
    def post(self, args):
        """
        Create a new team.
        """
        team = Team(**args)
        db.session.add(team)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            # TODO: handle errors better
            abort(code=http_exceptions.Conflict.code, message="Could not create a new team.")
        return team


@namespace.route('/<int:team_id>')
@api_v1.response(
    code=http_exceptions.NotFound.code,
    description="User not found.",
)
class TeamByID(Resource):
    """
    Manipulations with a specific team.
    """

    @api_v1.login_required(scopes=['teams:read'])
    @api_v1.response(schemas.DetailedTeamSchema())
    @api_v1.response(code=http_exceptions.Forbidden.code)
    def get(self, team_id):
        """
        Get team details by ID.
        """
        team = Team.query.get_or_404(team_id)
        with permissions.SupervisorRolePermission(obj=team):
            return team

    @api_v1.login_required(scopes=['teams:write'])
    @api_v1.parameters(parameters.PatchTeamDetailsParameters())
    @api_v1.response(schemas.DetailedTeamSchema())
    @api_v1.response(code=http_exceptions.Conflict.code)
    def patch(self, args, team_id):
        """
        Patch team details by ID.
        """
        team = Team.query.get_or_404(team_id)

        with permissions.OwnerRolePermission(obj=team):
            with permissions.WriteAccessPermission():
                state = {'current_password': None}

                for operation in args['body']:
                    if not self._process_patch_operation(operation, team=team, state=state):
                        log.info("Team patching has ignored unknown operation %s", operation)

                db.session.merge(team)
                try:
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    db.session.rollback()
                    # TODO: handle errors better
                    abort(
                        code=http_exceptions.Conflict.code,
                        message="Could not update team details."
                    )
        return user

    def _process_patch_operation(self, operation, team, state):
        """
        Args:
            operation (dict) - one patch operation in RFC 6902 format
            team (Team) - team instance which is needed to be patched
            state (dict) - inter-operations state storage

        Returns:
            processing_status (bool) - True if operation was handled, otherwise False.
        """
        if 'value' not in operation:
            # TODO: handle errors better
            abort(code=http_exceptions.UnprocessableEntity.code, message="value is required")
        assert operation['path'][0] == '/', "Path must always begin with /"
        field_name = operation['path'][1:]
        field_value = operation['value']

        if operation['op'] == parameters.PatchTeamDetailsParameters.OP_ADD:
            if field_name == Team.members.key:
                # TODO: add a user with ID `field_value` to a team members list
                raise NotImplementedError()
            return False

        if operation['op'] == parameters.PatchTeamDetailsParameters.OP_DELETE:
            if field_name == Team.members.key:
                # TODO: remove a user with ID `field_value` from a team members list
                raise NotImplementedError()
            return False

        if operation['op'] == parameters.PatchTeamDetailsParameters.OP_REPLACE:
            setattr(team, field_name, field_value)
            return True

        return False
