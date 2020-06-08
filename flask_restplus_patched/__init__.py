# -*- coding: utf-8 -*-
from flask_restplus import *  # NOQA
from .api import Api
from .model import Schema, DefaultHTTPErrorSchema

try:
    from .model import ModelSchema
except ImportError:
    pass
from .namespace import Namespace
from .parameters import Parameters, PostFormParameters, PatchJSONParameters
from .swagger import Swagger
from .resource import Resource
