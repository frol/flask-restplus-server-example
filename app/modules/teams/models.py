# encoding: utf-8

from sqlalchemy_utils import Timestamp

from app.extensions import db


team_members = db.Table('team_members',
    db.Column('team_id', db.Integer, db.ForeignKey('team.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class Team(db.Model, Timestamp):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(length=50), nullable=False)

    members = db.relationship(
        'User',
        secondary=team_members,
        backref=db.backref('teams', lazy='dynamic')
    )
