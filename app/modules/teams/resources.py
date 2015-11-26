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
from app.modules.users.models import User

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
    description="Team not found.",
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

    @api_v1.login_required(scopes=['teams:write'])
    @api_v1.response(code=http_exceptions.Conflict.code)
    def delete(self, team_id):
        """
        Delete a team by ID.
        """
        team = Team.query.get_or_404(team_id)

        with permissions.OwnerRolePermission(obj=team):
            with permissions.WriteAccessPermission():
                db.session.delete(team)

        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            # TODO: handle errors better
            abort(
                code=http_exceptions.Conflict.code,
                message="Could not delete the team."
            )

        return None

    def _process_patch_operation(self, operation, team, state):
        """
        Args:
            operation (dict) - one patch operation in RFC 6902 format.
            team (Team) - team instance which is needed to be patched.
            state (dict) - inter-operations state storage.

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
                user = User.query.get(field_value)
                if user is None:
                    abort(
                        code=http_exceptions.UnprocessableEntity.code,
                        message="User with id %s does not exist" % field_value
                    )
                team.members.append(user)
                return True
            return False

        if operation['op'] == parameters.PatchTeamDetailsParameters.OP_DELETE:
            if field_name == Team.members.key:
                user = User.query.get(field_value)
                if user is None:
                    abort(
                        code=http_exceptions.UnprocessableEntity.code,
                        message="User with id %s does not exist" % field_value
                    )
                team.members.remove(user)
                return True
            return False

        if operation['op'] == parameters.PatchTeamDetailsParameters.OP_REPLACE:
            setattr(team, field_name, field_value)
            return True

        return False


@namespace.route('/<int:team_id>/members/')
@api_v1.response(
    code=http_exceptions.NotFound.code,
    description="Team not found.",
)
class TeamMembers(Resource):
    """
    Manipulations with members of a specific team.
    """

    @api_v1.login_required(scopes=['teams:read'])
    @api_v1.parameters(PaginationParameters())
    @api_v1.response(schemas.BaseTeamMemberSchema(many=True))
    @api_v1.response(code=http_exceptions.Forbidden.code)
    def get(self, args, team_id):
        """
        Get team members by team ID.
        """
        team = Team.query.get_or_404(team_id)
        with permissions.SupervisorRolePermission(obj=team):
            return team.members[args['offset']: args['offset'] + args['limit']]

    @api_v1.login_required(scopes=['teams:write'])
    @api_v1.parameters(parameters.AddTeamMemberParameters())
    @api_v1.response(code=http_exceptions.Conflict.code)
    def post(self, args, team_id):
        """
        Add a new member to a team.
        """
        team = Team.query.get_or_404(team_id)

        with permissions.OwnerRolePermission(obj=team):
            with permissions.WriteAccessPermission():
                user = User.query.get(args['user_id'])
                if user is None:
                    abort(
                        code=http_exceptions.NotFound.code,
                        message="User with id %d does not exist" % args['user_id']
                    )
                team.members.append(user)
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

        return None


@namespace.route('/<int:team_id>/members/<int:user_id>')
@api_v1.response(
    code=http_exceptions.NotFound.code,
    description="Team or member not found.",
)
class TeamMemberByID(Resource):
    """
    Manipulations with a specific team member.
    """

    @api_v1.login_required(scopes=['teams:write'])
    @api_v1.response(code=http_exceptions.Conflict.code)
    def delete(self, args, team_id):
        """
        Remove a member from a team.
        """
        team = Team.query.get_or_404(team_id)

        with permissions.OwnerRolePermission(obj=team):
            with permissions.WriteAccessPermission():
                user = User.query.get(args['user_id'])
                if user is None:
                    abort(
                        code=http_exceptions.NotFound.code,
                        message="User with id %d does not exist" % args['user_id']
                    )
                team.members.remove(user)
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
