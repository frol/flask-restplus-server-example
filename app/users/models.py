from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import generate_password_hash, check_password_hash
import sqlalchemy

from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(length=80), unique=True, nullable=False)
    password = db.Column(db.String(length=128), nullable=False)
    email = db.Column(db.String(length=120), unique=True, nullable=False)

    first_name = db.Column(db.String(length=30), default='', nullable=False)
    middle_name = db.Column(db.String(length=30), default='', nullable=False)
    last_name = db.Column(db.String(length=30), default='', nullable=False)

    SR_ACTIVATED = 0x2000
    SR_READONLY = 0x4000
    SR_ADMIN = 0x8000
    DEFAULT_STATIC_ROLES_CHOICES = (
        (SR_ACTIVATED, "Activated"),
        (SR_READONLY, "Read-only"),
        (SR_ADMIN, "Admin"),
    )

    static_roles = db.Column(db.Integer, default=0, nullable=False)

    def __init__(self, **kwargs):
        password = kwargs.pop('password', None)
        super(User, self).__init__(**kwargs)
        if password is not None:
            self.set_password(password)

    def __repr__(self):
        return (
            "<{class_name}("
            "id={self.id}, "
            "username=\"{self.username}\", "
            "email=\"{self.email}\", "
            "is_active={self.is_active}, "
            "is_readonly={self.is_readonly}, "
            "is_admin={self.is_admin}"
            ")>".format(
                class_name=self.__class__.__name__,
                self=self
            )
        )

    def save(self):
        db.session.merge(self)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            raise

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password, commit=True):
        self.password = generate_password_hash(password)
        if commit and self.id:
            self.save()

    def has_static_role(self, role):
        return (self.static_roles & role) != 0

    def set_static_role(self, role, commit=True):
        if self.has_static_role(role):
            return
        self.static_roles |= role
        if commit and self.id:
            self.save()

    def unset_static_role(self, role, commit=True):
        if not self.has_static_role(role):
            return
        self.static_roles ^= role
        if commit and self.id:
            self.save()

    def check_owner(self, user):
        return self.id == user.id

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return self.has_static_role(self.SR_ACTIVATED)

    @property
    def is_readonly(self):
        return self.has_static_role(self.SR_READONLY)

    @property
    def is_admin(self):
        return self.has_static_role(self.SR_ADMIN)

    @classmethod
    def create(cls, username, password, email, **kwargs):
        new_user = cls(username=username, password=password, email=email, **kwargs)
        db.session.add(new_user)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            return None
        return new_user

    @classmethod
    def find_with_password(cls, username, password):
        user = cls.query.filter_by(username=username).first()
        if not user:
            return None
        if user.verify_password(password):
            return user
        return None
