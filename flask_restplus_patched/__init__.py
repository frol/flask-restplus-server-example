# -*- coding: utf-8 -*-
from flask_restplus import *  # NOQA
from .api import Api  # NOQA
from .model import Schema, DefaultHTTPErrorSchema  # NOQA

try:
    from .model import ModelSchema  # NOQA
except ImportError:
    pass
from .namespace import Namespace  # NOQA
from .parameters import Parameters, PostFormParameters, PatchJSONParameters  # NOQA
from .swagger import Swagger  # NOQA
from .resource import Resource  # NOQA
