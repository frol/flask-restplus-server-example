try:
    from http import HTTPStatus
except ImportError:
    class HTTPStatus:
        NO_CONTENT = 204
        ACCEPTED = 202
