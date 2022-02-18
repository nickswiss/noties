import os
import logging
import json

from aws_utils.lambda_functions.http.decorators import rest_api
from aws_utils.lambda_functions.http.response import HTTPResponse
from aws_utils.secrets_manager import get_secret

GMAIL_OAUTH_SECRET = os.getenv('GMAIL_OAUTH_SECRET')
OAUTH_FORM = os.path.join(os.path.dirname(__file__), "oauth_form.html")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def oauth_form():
    with open(OAUTH_FORM, "r") as f:
        template = f.read()
    return template


@rest_api
def lambda_handler(request):
    gmail_oauth_config = json.loads(get_secret(GMAIL_OAUTH_SECRET))
    logging.info(gmail_oauth_config['web']['token_uri'])
    return HTTPResponse(data=oauth_form(), headers={'Content-Type': 'text/html'})
