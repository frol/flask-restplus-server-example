from apispec.ext.marshmallow.swagger import schema2parameters
from flask_restplus.swagger import Swagger as OriginalSwagger


class Swagger(OriginalSwagger):

    def _parameters_to_swagger(self, schema):
        if not schema:
            return []
        if isinstance(schema, list):
            return schema
        if isinstance(schema, dict) and all(isinstance(field, dict) for field in schema.values()):
            return list(schema.values())

        return schema2parameters(
            schema,
            default_in='body' if schema.many else 'query',
            required=True,
            dump=False
        )

    def parameters_for(self, doc, method):
        swagger_doc_params = self._parameters_to_swagger(doc['params'])
        swagger_doc_method_params = self._parameters_to_swagger(doc[method]['params'])
        return swagger_doc_params + swagger_doc_method_params
