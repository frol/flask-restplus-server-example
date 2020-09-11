# -*- coding: utf-8 -*-
"""
Serialization schemas for Submissions resources RESTful API
----------------------------------------------------
"""

from flask_restplus_patched import ModelSchema

from .models import Submission


class BaseSubmissionSchema(ModelSchema):
    """
    Base Submission schema exposes only the most general fields.
    """

    class Meta:
        # pylint: disable=missing-docstring
        model = Submission
        fields = (
            Submission.guid.key,
            Submission.commit.key,
            Submission.major_type.key,
            Submission.title.key,
            Submission.description.key,
        )
        dump_only = (
            Submission.guid.key,
            Submission.commit.key,
        )


class DetailedSubmissionSchema(BaseSubmissionSchema):
    """
    Detailed Submission schema exposes all useful fields.
    """

    class Meta(BaseSubmissionSchema.Meta):
        fields = BaseSubmissionSchema.Meta.fields + (
            Submission.owner_guid.key,
            Submission.created.key,
            Submission.updated.key,
        )
        dump_only = BaseSubmissionSchema.Meta.dump_only + (
            Submission.owner_guid.key,
            Submission.created.key,
            Submission.updated.key,
        )
