from builtins import Exception
from .constants import DEFAULT_ERROR_CODE, DEFAULT_ERROR_MESSAGE, DEFAULT_HEADERS
from .status import HTTP_400_BAD_REQUEST, HTTP_403_UNAUTHORIZED


class Base(Exception):
    error_message = DEFAULT_ERROR_MESSAGE
    status_code = DEFAULT_ERROR_CODE
    headers = DEFAULT_HEADERS


class ValidationException(Base):
    error_message = "There was an error handling your request."
    status_code = HTTP_400_BAD_REQUEST

    def __init__(self, message=None, code=None):
        super().__init__(message, code)
        self.error_message = message or self.error_message
        self.status_code = code or self.status_code


class UnauthorizedException(Base):
    error_message = "Unauthorized"
    status_code = HTTP_403_UNAUTHORIZED
