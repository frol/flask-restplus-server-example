# encoding: utf-8
"""
Team database models
--------------------
"""

from sqlalchemy_utils import Timestamp

from app.extensions import db


class TeamMember(db.Model):
    """
    Team-member database model.
    """
    __tablename__ = 'team_member'

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)
    team = db.relationship(
        'Team',
        backref=db.backref('members', cascade='delete, delete-orphan')
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship(
        'User',
        backref=db.backref('teams_membership', cascade='delete, delete-orphan')
    )

    is_leader = db.Column(db.Boolean(name='is_leader'), default=False, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(team_id, user_id),
    )

    def __repr__(self):
        return (
            "<{class_name}("
            "team_id={self.team_id}, "
            "user_id=\"{self.user_id}\", "
            "is_leader=\"{self.is_leader}\""
            ")>".format(
                class_name=self.__class__.__name__,
                self=self
            )
        )

    def check_owner(self, user):
        return self.user == user

    def check_supervisor(self, user):
        return self.team.check_owner(user)


class Team(db.Model, Timestamp):
    """
    Team database model.
    """

    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    title = db.Column(db.String(length=50), nullable=False)

    def __repr__(self):
        return (
            "<{class_name}("
            "id={self.id}, "
            "title=\"{self.title}\""
            ")>".format(
                class_name=self.__class__.__name__,
                self=self
            )
        )

    @db.validates('title')
    def validate_title(self, key, title):  # pylint: disable=unused-argument,no-self-use
        if len(title) < 3:
            raise ValueError("Title has to be at least 3 characters long.")
        return title

    def check_owner(self, user):
        """
        This is a helper method for OwnerRolePermission integration.
        """
        if db.session.query(
                TeamMember.query.filter_by(team=self, is_leader=True, user=user).exists()
        ).scalar():
            return True
        return False
