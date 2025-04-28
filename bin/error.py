# Imports
import bin.config
from sqlalchemy.exc import DontWrapMixin
import traceback
import logging
import http

# Attributes
cfg = bin.config.Config()
log = logging.getLogger(cfg.NAME)

# Exceptions
class APIError(Exception, DontWrapMixin):
    def __init__(self, message, status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR.value):
        Exception.__init__(self)

        self.status_code = status_code

        log.error(message)
        log.debug(traceback.format_exc())

class AlertError(Exception):
    def __init__(self, message):
        Exception.__init__(self)

        log.error(message)
        log.debug(traceback.format_exc())

class UploadError(Exception):
    def __init__(self, message):
        Exception.__init__(self)

        log.error(message)
        log.debug(traceback.format_exc())
