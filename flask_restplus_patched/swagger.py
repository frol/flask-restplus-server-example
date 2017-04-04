from apispec.ext.marshmallow.swagger import schema2parameters
from flask_restplus.swagger import Swagger as OriginalSwagger


class Swagger(OriginalSwagger):

    def parameters_for(self, doc):
        schema = doc['params']

        if not schema:
            return []
        if isinstance(schema, list):
            return schema
        if isinstance(schema, dict) and all(isinstance(field, dict) for field in schema.values()):
            return list(schema.values())

        if 'in' in schema.context and 'json' in schema.context['in']:
            default_location = 'body'
        else:
            default_location = 'query'
        return schema2parameters(schema, default_in=default_location, required=True)
