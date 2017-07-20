# encoding: utf-8
# pylint: disable=bad-continuation
"""
RESTful API Team resources
--------------------------
"""

import logging
import time

from flask import request

from app.extensions.api import Namespace
from app.service.alioss import upload as oss_upload
from flask_restplus_patched import Resource

log = logging.getLogger(__name__)  # pylint: disable=invalid-name
api = Namespace('evidences', description="Evidences")  # pylint: disable=invalid-name


@api.route('/')
class Evidences(Resource):
    """
    Manipulations with teams.
    """


@api.route('/photo')
class Evidences(Resource):

    def post(self):
        # 上传图片
        file = request.files.get('file')
        if file:
            current_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            key = "uploads/" + current_date + "/" + str(time.time()) + "_" + file.filename
            oss_file = oss_upload(key, file)

        return None
