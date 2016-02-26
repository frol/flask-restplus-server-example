# encoding: utf-8
# pylint: disable=missing-docstring
from six import itervalues

from flask_marshmallow import Schema, base_fields
from marshmallow import validate


class Parameters(Schema):

    def __init__(self, **kwargs):
        super(Parameters, self).__init__(strict=True, **kwargs)

    def __contains__(self, field):
        return field in self.fields

    def make_instance(self, data):
        # pylint: disable=unused-argument
        """
        This is a no-op function which shadows ``ModelSchema.make_instance``
        method (when inherited classes inherit from ``ModelSchema``). Thus, we
        avoid a new instance creation because it is undesirable behaviour for
        parameters (they can be used not only for saving new instances).
        """
        return


class PostFormParameters(Parameters):

    def __init__(self, *args, **kwargs):
        super(PostFormParameters, self).__init__(*args, **kwargs)
        for field in itervalues(self.fields):
            field.metadata['location'] = 'form'


class PatchJSONParameters(Parameters):
    """
    Base parameters class for handling PATCH arguments according to RFC 6902.
    """

    # All operations described in RFC 6902
    OP_ADD = 'add'
    OP_REMOVE = 'remove'
    OP_REPLACE = 'replace'
    OP_MOVE = 'move'
    OP_COPY = 'copy'
    OP_TEST = 'test'

    # However, we use only those which make sense in RESTful API
    OPERATION_CHOICES = (
        OP_TEST,
        OP_ADD,
        OP_REMOVE,
        OP_REPLACE,
    )
    op = base_fields.String(required=True) # pylint: disable=invalid-name

    PATH_CHOICES = None
    path = base_fields.String(required=True)

    value = base_fields.Raw(required=False)

    def __init__(self, *args, **kwargs):
        super(PatchJSONParameters, self).__init__(*args, many=True, **kwargs)
        if not self.PATH_CHOICES:
            raise ValueError("%s.PATH_CHOICES has to be set" % self.__class__.__name__)
        # Make a copy of `validators` as otherwise we will modify the behaviour
        # of all `marshmallow.Schema`-based classes
        self.fields['op'].validators = \
            self.fields['op'].validators + [validate.OneOf(self.OPERATION_CHOICES)]
        self.fields['path'].validators = \
            self.fields['path'].validators + [validate.OneOf(self.PATH_CHOICES)]
