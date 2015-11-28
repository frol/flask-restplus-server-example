# encoding: utf-8

from sqlalchemy_utils import Timestamp

from app.extensions import db


class TeamMember(db.Model):
    __tablename__ = 'team_member'

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)
    team = db.relationship('Team')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User', backref='teams_membership')

    is_leader = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('team_id', 'user_id', name='_team_user_uc'),
    )

    def check_owner(self, user):
        return self.user == user

    def check_supervisor(self, user):
        return self.team.check_owner(user)


class Team(db.Model, Timestamp):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(length=50), nullable=False)

    members = db.relationship('TeamMember')

    def check_owner(self, user):
        if db.session.query(
            TeamMember.query.filter_by(team=self, is_leader=True, user=user).exists()
        ).scalar():
            return True
        return False
