# encoding: utf-8

from flask.ext.marshmallow import base_fields
from flask_restplus_patched import Parameters


class PaginationParameters(Parameters):

    limit = base_fields.Integer(missing=20)
    offset = base_fields.Integer(missing=0)
