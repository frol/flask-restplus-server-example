# encoding: utf-8
# pylint: disable=bad-continuation
"""
RESTful API Team resources
--------------------------
"""

import logging

from flask_login import current_user
from flask_restplus_patched import Resource
from flask_restplus._http import HTTPStatus

from app.extensions import db
from app.extensions.api import Namespace, abort
from app.modules.users import permissions
from app.modules.users.models import User


from . import parameters, schemas
from .models import Team, TeamMember


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('teams', description="Teams")  # pylint: disable=invalid-name


@api.route('/')
@api.login_required(oauth_scopes=['teams:read'])
class Teams(Resource):
    """
    Manipulations with teams.
    """
    @api.response(schemas.BaseTeamSchema(many=True))
    @api.paginate()
    def get(self, args):
        """
        List of teams.

        Returns a list of teams starting from ``offset`` limited by ``limit``
        parameter.
        """
        return Team.query

    @api.login_required(oauth_scopes=['teams:write'])
    @api.parameters(parameters.CreateTeamParameters())
    @api.response(schemas.DetailedTeamSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def post(self, args):
        """
        Create a new team.
        """
        with api.commit_or_abort(
                db.session,
                default_error_message="Failed to create a new team"
            ):
            team = Team(**args)
            db.session.add(team)
            team_member = TeamMember(team=team, user=current_user, is_leader=True)
            db.session.add(team_member)
        return team


@api.route('/<int:team_id>')
@api.login_required(oauth_scopes=['teams:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND,
    description="Team not found.",
)
@api.resolve_object_by_model(Team, 'team')
class TeamByID(Resource):
    """
    Manipulations with a specific team.
    """

    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['team']}
    )
    @api.response(schemas.DetailedTeamSchema())
    def get(self, team):
        """
        Get team details by ID.
        """
        return team

    @api.login_required(oauth_scopes=['teams:write'])
    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['team']}
    )
    @api.permission_required(permissions.WriteAccessPermission())
    @api.parameters(parameters.PatchTeamDetailsParameters())
    @api.response(schemas.DetailedTeamSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def patch(self, args, team):
        """
        Patch team details by ID.
        """
        with api.commit_or_abort(
                db.session,
                default_error_message="Failed to update team details."
            ):
            parameters.PatchTeamDetailsParameters.perform_patch(args, obj=team)
            db.session.merge(team)
        return team

    @api.login_required(oauth_scopes=['teams:write'])
    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['team']}
    )
    @api.permission_required(permissions.WriteAccessPermission())
    @api.response(code=HTTPStatus.CONFLICT)
    @api.response(code=HTTPStatus.NO_CONTENT)
    def delete(self, team):
        """
        Delete a team by ID.
        """
        with api.commit_or_abort(
                db.session,
                default_error_message="Failed to delete the team."
            ):
            db.session.delete(team)
        return None


@api.route('/<int:team_id>/members/')
@api.login_required(oauth_scopes=['teams:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND,
    description="Team not found.",
)
@api.resolve_object_by_model(Team, 'team')
class TeamMembers(Resource):
    """
    Manipulations with members of a specific team.
    """

    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['team']}
    )
    @api.permission_required(permissions.OwnerRolePermission(partial=True))
    @api.response(schemas.BaseTeamMemberSchema(many=True))
    @api.paginate()
    def get(self, args, team):
        """
        Get team members by team ID.
        """
        return TeamMember.query.filter_by(team=team)

    @api.login_required(oauth_scopes=['teams:write'])
    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['team']}
    )
    @api.permission_required(permissions.WriteAccessPermission())
    @api.parameters(parameters.AddTeamMemberParameters())
    @api.response(schemas.BaseTeamMemberSchema())
    @api.response(code=HTTPStatus.CONFLICT)
    def post(self, args, team):
        """
        Add a new member to a team.
        """
        with api.commit_or_abort(
                db.session,
                default_error_message="Failed to update team details."
            ):
            user_id = args.pop('user_id')
            user = User.query.get(user_id)
            if user is None:
                abort(
                    code=HTTPStatus.NOT_FOUND,
                    message="User with id %d does not exist" % user_id
                )

            team_member = TeamMember(team=team, user=user, **args)
            db.session.add(team_member)

        return team_member


@api.route('/<int:team_id>/members/<int:user_id>')
@api.login_required(oauth_scopes=['teams:read'])
@api.response(
    code=HTTPStatus.NOT_FOUND,
    description="Team or member not found.",
)
@api.resolve_object_by_model(Team, 'team')
class TeamMemberByID(Resource):
    """
    Manipulations with a specific team member.
    """

    @api.login_required(oauth_scopes=['teams:write'])
    @api.permission_required(
        permissions.OwnerRolePermission,
        kwargs_on_request=lambda kwargs: {'obj': kwargs['team']}
    )
    @api.permission_required(permissions.WriteAccessPermission())
    @api.response(code=HTTPStatus.CONFLICT)
    def delete(self, team, user_id):
        """
        Remove a member from a team.
        """
        with api.commit_or_abort(
                db.session,
                default_error_message="Failed to update team details."
            ):
            team_member = TeamMember.query.filter_by(team=team, user_id=user_id).first_or_404()
            db.session.delete(team_member)

        return None
