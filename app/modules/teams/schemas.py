# encoding: utf-8
"""
Serialization schemas for Team resources RESTful API
----------------------------------------------------
"""

from flask_marshmallow import base_fields
from flask_restplus_patched import ModelSchema

from app.modules.users.schemas import BaseUserSchema

from .models import Team, TeamMember


class BaseTeamSchema(ModelSchema):
    """
    Base team schema exposes only the most general fields.
    """

    class Meta:
        # pylint: disable=missing-docstring
        model = Team
        fields = (
            Team.id.key,
            Team.title.key,
        )
        dump_only = (
            Team.id.key,
        )


class DetailedTeamSchema(BaseTeamSchema):
    """
    Detailed team schema exposes all useful fields.
    """

    members = base_fields.Nested(
        'BaseTeamMemberSchema',
        exclude=(TeamMember.team.key, ),
        many=True
    )

    class Meta(BaseTeamSchema.Meta):
        fields = BaseTeamSchema.Meta.fields + (
            Team.members.key,
            Team.created.key,
            Team.updated.key,
        )


class BaseTeamMemberSchema(ModelSchema):

    team = base_fields.Nested(BaseTeamSchema)
    user = base_fields.Nested(BaseUserSchema)

    class Meta:
        model = TeamMember
        fields = (
            TeamMember.team.key,
            TeamMember.user.key,
            TeamMember.is_leader.key,
        )
