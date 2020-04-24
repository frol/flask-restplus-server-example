# coding: utf-8
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""
from flask import Blueprint
import logging

from .views import FRONTEND_STATIC_ROOT

log = logging.getLogger(__name__)

frontend_blueprint = Blueprint('frontend', __name__, url_prefix='/', static_url_path='', static_folder=FRONTEND_STATIC_ROOT)          # pylint: disable=invalid-name


@frontend_blueprint.route('/', methods=['GET'])
def home(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint offers the home page html
    """
    return frontend_blueprint.send_static_file('index.html')
