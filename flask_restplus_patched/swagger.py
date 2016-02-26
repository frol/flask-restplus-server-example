from apispec.ext.marshmallow.swagger import schema2parameters
from flask_restplus.swagger import Swagger as OriginalSwagger


class Swagger(OriginalSwagger):

    def _parameters_to_swagger(self, schema, method):
        if not schema:
            return []
        if isinstance(schema, list):
            return schema
        if isinstance(schema, dict) and all(isinstance(field, dict) for field in schema.values()):
            return list(schema.values())

        if method == 'post':
            default_location = 'formData'
        elif schema.many:
            default_location = 'body'
        else:
            default_location = 'query'
        return schema2parameters(schema, default_in=default_location, required=True, dump=False)

    def parameters_for(self, doc, method):
        swagger_doc_params = self._parameters_to_swagger(doc['params'], method)
        swagger_doc_method_params = self._parameters_to_swagger(doc[method]['params'], method)
        return swagger_doc_params + swagger_doc_method_params
