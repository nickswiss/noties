import json

from .status import HTTP_200_OK


class HTTPResponse:
    def __init__(self, data=None, headers=None, status=HTTP_200_OK):
        self.body = data
        self.status = status
        self.headers = headers

    def to_rest(self):
        body = self.body
        if self.body is not None and not isinstance(self.body, str):
            body = json.dumps(self.body)

        return {"statusCode": self.status, "headers": self.headers, "body": body}
