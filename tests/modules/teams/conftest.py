# encoding: utf-8

import pytest


@pytest.yield_fixture()
def team_for_regular_user(db, regular_user, readonly_user):
    from app.modules.teams.models import Team, TeamMember

    team = Team(title="Regular User's team")
    regular_user_team_member = TeamMember(team=team, user=regular_user, is_leader=True)
    readonly_user_team_member = TeamMember(team=team, user=readonly_user)
    with db.session.begin():
        db.session.add(team)
        db.session.add(regular_user_team_member)
        db.session.add(readonly_user_team_member)

    yield team

    # Cleanup
    with db.session.begin():
        db.session.delete(readonly_user_team_member)
        db.session.delete(regular_user_team_member)
        db.session.delete(team)


@pytest.yield_fixture()
def team_for_nobody(db):
    """
    Create a team that not belongs to regural user
    """
    from app.modules.teams.models import Team

    team = Team(title="Admin User's team")
    with db.session.begin():
        db.session.add(team)

    yield team

    # Cleanup
    with db.session.begin():
        db.session.delete(team)
