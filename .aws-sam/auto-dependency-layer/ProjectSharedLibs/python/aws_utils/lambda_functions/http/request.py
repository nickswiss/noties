import json

from .constants import SAFE_METHODS


class HTTPRequest:
    def __init__(self, event, context):
        self._event = event
        self._context = context
        self.method = event.get("httpMethod", "GET")
        self.path = event.get("path")
        self.path_params = event.get("pathParameters")
        self.headers = {key.upper(): value for key, value in event.get("headers").items()}
        self.query_string_params = event.get("queryStringParameters", {})
        self.multi_val_query_string_params = event.get(
            "multiValueQueryStringParameters", {}
        )

        self.body = None
        if self.method.upper() not in SAFE_METHODS:
            self.body = event["body"]
        try:
            self.content = json.loads(self.body)
        except TypeError:
            self.content = None
