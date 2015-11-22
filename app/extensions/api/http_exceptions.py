from flask_restplus_patched import Api, abort as restplus_abort
from werkzeug.exceptions import Unauthorized, Forbidden, NotFound, UnprocessableEntity


API_DEFAULT_HTTP_CODE_MESSAGES = {
    Unauthorized.code: (
        "The server could not verify that you are authorized to access the "
        "URL requested. You either supplied the wrong credentials (e.g. a bad "
        "password), or your browser doesn't understand how to supply the "
        "credentials required."
    ),
    Forbidden.code: (
        "You don't have the permission to access the requested resource."
    ),
    NotFound.code: NotFound.description,
    UnprocessableEntity.code: UnprocessableEntity.description,
}


def abort(code, message=None, **kwargs):
    if message is None:
        message = API_DEFAULT_HTTP_CODE_MESSAGES.get(code)
    restplus_abort(code=code, message=message)
