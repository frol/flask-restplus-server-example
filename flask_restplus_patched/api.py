from flask.ext import restful, marshmallow
from flask.ext.restplus import Api as OriginalApi
from flask_restplus.utils import merge
from werkzeug import cached_property


from .model import ApiModel
from .swagger import Swagger


class Api(OriginalApi):

    @cached_property
    def __schema__(self):
        return Swagger(self).as_dict()

    def _handle_api_doc(self, cls, doc):
        if doc is False:
            cls.__apidoc__ = False
            return
        ##unshortcut_params_description(doc)
        ##for key in 'get', 'post', 'put', 'delete', 'options', 'head', 'patch':
        ##    if key in doc:
        ##        if doc[key] is False:
        ##            continue
        ##        unshortcut_params_description(doc[key])
        cls.__apidoc__ = merge(getattr(cls, '__apidoc__', {}), doc)

    def model(self, name=None, model=None, **kwargs):
        """
        Register a model
        """
        if isinstance(model, marshmallow.Schema):
            api_model = ApiModel(model)
            api_model.__apidoc__ = kwargs
            api_model.__apidoc__['name'] = name = name or model.__class__.__name__
            self.models[name] = api_model
            return api_model
        return super(Api, self).model(name, model, **kwargs)


# This function is moved out from Api class
def abort(code=500, message=None, **kwargs):
    '''Properly abort the current request'''
    if message or kwargs and 'status' not in kwargs:
        kwargs['status'] = code
    if message:
        kwargs['message'] = str(message)
    restful.abort(code, **kwargs)
