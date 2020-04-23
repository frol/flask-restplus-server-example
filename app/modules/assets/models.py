# encoding: utf-8
"""
Assets database models
--------------------
"""
from flask import current_app
from sqlalchemy_utils import Timestamp
import os

from app.extensions import db


class Asset(db.Model, Timestamp):
    """
    Assets database model.
    """

    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    code = db.Column(db.String(length=64), nullable=False)
    ext  = db.Column(db.String(length=5), nullable=False)

    def __repr__(self):
        return (
            "<{class_name}("
            "id={self.id}, "
            "file=\"{self.code}{self.ext}\""
            ")>".format(
                class_name=self.__class__.__name__,
                self=self
            )
        )

    @property
    def absolute_filepath(self):
        asset_path = current_app.config.get('ASSET_DATABASE_PATH', None)
        asset_filname = '%s%s' % (self.code, self.ext, )
        asset_filepath = os.path.join(asset_path, asset_filname, )

        asset_filepath = os.path.abspath(asset_filepath)
        assert os.path.exists(asset_filepath)
        return asset_filepath
