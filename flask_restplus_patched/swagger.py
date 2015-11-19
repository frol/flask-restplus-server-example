from six import iteritems

from apispec.ext.marshmallow.swagger import fields2parameters
from flask_restplus.swagger import ref, Swagger as OriginalSwagger


class Swagger(OriginalSwagger):

    def _fields_to_swagger(self, fields):
        if not fields:
            return []
        if isinstance(fields, list):
            return fields
        if isinstance(fields, dict) and all(isinstance(field, dict) for field in fields.values()):
            return list(fields.values())

        if all(field.metadata.get('location') == 'json' for field_name, field in iteritems(fields)):
            default_in = 'body'
        else:
            default_in = 'query'

        parameters = fields2parameters(fields, default_in=default_in, required=True)
        # XXX: We use virtual 'body' argument due to the limitations of webargs:
        # https://github.com/sloria/webargs/issues/81
        # Here we drop 'body' argument, so Swagger spec will use a JSON list as
        # a top-level structure instead of unnecessary 'body' wrapper.
        if parameters and 'schema' in parameters[0] and 'body' in parameters[0]['schema']['properties']:
            parameters[0]['schema'] = parameters[0]['schema']['properties']['body']
        return parameters

    def parameters_for(self, doc, method):
        swagger_doc_params = self._fields_to_swagger(doc['params'])
        swagger_doc_method_params = self._fields_to_swagger(doc[method]['params'])
        return swagger_doc_params + swagger_doc_method_params
