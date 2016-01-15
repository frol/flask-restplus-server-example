# encoding: utf-8
# pylint: disable=missing-docstring

import pytest


@pytest.yield_fixture()
def team_for_regular_user(db, regular_user, readonly_user):
    # pylint: disable=invalid-name
    from app.modules.teams.models import Team, TeamMember

    team = Team(title="Regular User's team")
    db.session.add(team)
    regular_user_team_member = TeamMember(team=team, user=regular_user, is_leader=True)
    db.session.add(regular_user_team_member)
    readonly_user_team_member = TeamMember(team=team, user=readonly_user)
    db.session.add(readonly_user_team_member)
    db.session.commit()

    yield team

    # Cleanup
    db.session.delete(readonly_user_team_member)
    db.session.delete(regular_user_team_member)
    db.session.delete(team)
    db.session.commit()
