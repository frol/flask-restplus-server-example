# encoding: utf-8
"""
Serialization schemas for Team resources RESTful API
====================================================
"""

from flask_restplus_patched import ModelSchema
from flask.ext.marshmallow import base_fields

from app.modules.users.schemas import BaseUserSchema

from .models import Team, TeamMember


class BaseTeamSchema(ModelSchema):

    class Meta:
        model = Team
        fields = (
            Team.id.key,
            Team.title.key,
        )
        dump_only = (
            Team.id.key,
        )


class DetailedTeamSchema(BaseTeamSchema):

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
