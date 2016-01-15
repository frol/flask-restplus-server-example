# encoding: utf-8
# pylint: disable=no-self-use
"""
RESTful API Team resources
--------------------------
"""

import logging

from flask_restplus import Resource
import sqlalchemy

from app.extensions import db
from app.extensions.api import api_v1, abort, http_exceptions
from app.extensions.api.parameters import PaginationParameters
from app.modules.users import permissions
from app.modules.users.models import User

from . import parameters, schemas
from .models import Team, TeamMember


log = logging.getLogger(__name__) # pylint: disable=invalid-name
namespace = api_v1.namespace('teams', description="Teams") # pylint: disable=invalid-name


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
        # pylint: disable=no-member
        try:
            try:
                team = Team(**args)
            except ValueError as exception:
                abort(code=http_exceptions.Conflict.code, message=str(exception))
            db.session.add(team)
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                abort(code=http_exceptions.Conflict.code, message="Could not create a new team.")
        finally:
            db.session.rollback()
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
    @api_v1.permission_required(permissions.OwnerRolePermission(partial=True))
    @api_v1.response(schemas.DetailedTeamSchema())
    def get(self, team_id):
        """
        Get team details by ID.
        """
        team = Team.query.get_or_404(team_id)
        with permissions.OwnerRolePermission(obj=team):
            return team

    @api_v1.login_required(scopes=['teams:write'])
    @api_v1.permission_required(permissions.OwnerRolePermission(partial=True))
    @api_v1.parameters(parameters.PatchTeamDetailsParameters())
    @api_v1.response(schemas.DetailedTeamSchema())
    @api_v1.response(code=http_exceptions.Conflict.code)
    def patch(self, args, team_id):
        """
        Patch team details by ID.
        """
        team = Team.query.get_or_404(team_id)

        # pylint: disable=no-member
        try:
            with permissions.OwnerRolePermission(obj=team):
                with permissions.WriteAccessPermission():
                    for operation in args['body']:
                        try:
                            if not self._process_patch_operation(operation, team=team):
                                log.info(
                                    "Team patching has ignored unknown operation %s",
                                    operation
                                )
                        except ValueError as exception:
                            abort(code=http_exceptions.Conflict.code, message=str(exception))
                    db.session.merge(team)

            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                abort(
                    code=http_exceptions.Conflict.code,
                    message="Could not update team details."
                )
        finally:
            db.session.rollback()
        return team

    @api_v1.login_required(scopes=['teams:write'])
    @api_v1.permission_required(permissions.OwnerRolePermission(partial=True))
    @api_v1.response(code=http_exceptions.Conflict.code)
    def delete(self, team_id):
        """
        Delete a team by ID.
        """
        team = Team.query.get_or_404(team_id)

        # pylint: disable=no-member
        with permissions.OwnerRolePermission(obj=team):
            with permissions.WriteAccessPermission():
                db.session.delete(team)

        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            # TODO: handle errors better
            abort(
                code=http_exceptions.Conflict.code,
                message="Could not delete the team."
            )

        return None

    def _process_patch_operation(self, operation, team):
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
    @api_v1.permission_required(permissions.OwnerRolePermission(partial=True))
    @api_v1.parameters(PaginationParameters())
    @api_v1.response(schemas.BaseTeamMemberSchema(many=True))
    def get(self, args, team_id):
        """
        Get team members by team ID.
        """
        team = Team.query.get_or_404(team_id)
        with permissions.OwnerRolePermission(obj=team):
            return team.members[args['offset']: args['offset'] + args['limit']]

    @api_v1.login_required(scopes=['teams:write'])
    @api_v1.permission_required(permissions.OwnerRolePermission(partial=True))
    @api_v1.parameters(parameters.AddTeamMemberParameters())
    @api_v1.response(schemas.BaseTeamMemberSchema())
    @api_v1.response(code=http_exceptions.Conflict.code)
    def post(self, args, team_id):
        """
        Add a new member to a team.
        """
        team = Team.query.get_or_404(team_id)

        # pylint: disable=no-member
        try:
            with permissions.OwnerRolePermission(obj=team):
                with permissions.WriteAccessPermission():
                    user_id = args.pop('user_id')
                    user = User.query.get(user_id)
                    if user is None:
                        abort(
                            code=http_exceptions.NotFound.code,
                            message="User with id %d does not exist" % user_id
                        )
                    try:
                        team_member = TeamMember(team=team, user=user, **args)
                    except ValueError as exception:
                        abort(code=http_exceptions.Conflict.code, message=str(exception))
                    db.session.add(team_member)

            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                abort(
                    code=http_exceptions.Conflict.code,
                    message="Could not update team details."
                )
        finally:
            db.session.rollback()
        return team_member


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
    @api_v1.permission_required(permissions.OwnerRolePermission(partial=True))
    @api_v1.response(code=http_exceptions.Conflict.code)
    def delete(self, team_id, user_id):
        """
        Remove a member from a team.
        """
        team = Team.query.get_or_404(team_id)

        # pylint: disable=no-member
        with permissions.OwnerRolePermission(obj=team):
            with permissions.WriteAccessPermission():
                team_member = TeamMember.query.filter_by(team=team, user_id=user_id).one()
                if team_member is None:
                    abort(
                        code=http_exceptions.NotFound.code,
                        message="User with id %d does not exist" % user_id
                    )
                db.session.delete(team_member)

        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            # TODO: handle errors better
            abort(
                code=http_exceptions.Conflict.code,
                message="Could not update team details."
            )

        return None
