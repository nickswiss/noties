from functools import wraps

from .request import HTTPRequest
from .exceptions import ValidationException, UnauthorizedException, Base
from .response import HTTPResponse
from .constants import DEFAULT_ERROR_MESSAGE, DEFAULT_ERROR_CODE, DEFAULT_HEADERS

import logging

log = logging.getLogger(__name__)


def rest_api(f):
    @wraps(f)
    def lambda_handler(event, context, *args, **kwargs):
        try:
            request = HTTPRequest(event, context)
            response = f(request, *args, **kwargs)
            return response.to_rest()
        except (ValidationException, UnauthorizedException, Base) as e:
            return HTTPResponse(
                data=e.error_message, status=e.status_code, headers=e.headers
            ).to_rest()
        except Exception as e:
            log.error(
                {
                    "resource": "http",
                    "operation": "rest_api",
                    "message": "An uncaught error has occured",
                    "error": e,
                    "details": {
                        "event": event,
                        "context": context,
                        "args": args,
                        "kwargs": kwargs,
                    },
                }
            )
            return HTTPResponse(
                data=DEFAULT_ERROR_MESSAGE,
                status=DEFAULT_ERROR_CODE,
                headers=DEFAULT_HEADERS,
            ).to_rest()

    return lambda_handler
