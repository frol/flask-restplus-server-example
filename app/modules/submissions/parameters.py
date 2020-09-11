# -*- coding: utf-8 -*-
"""
Input arguments (Parameters) for Submissions resources RESTful API
-----------------------------------------------------------
"""

from flask_restplus_patched import Parameters, PatchJSONParameters

from . import schemas
from .models import Submission


class CreateSubmissionParameters(Parameters, schemas.DetailedSubmissionSchema):
    class Meta(schemas.DetailedSubmissionSchema.Meta):
        pass


class PatchSubmissionDetailsParameters(PatchJSONParameters):
    # pylint: disable=abstract-method,missing-docstring
    OPERATION_CHOICES = (PatchJSONParameters.OP_REPLACE,)

    PATH_CHOICES = tuple('/%s' % field for field in (Submission.title.key,))
