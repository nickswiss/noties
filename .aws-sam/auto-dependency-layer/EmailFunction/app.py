import os
import logging
import json

from aws_utils.secrets_manager import get_secret

GMAIL_OAUTH_SECRET = os.getenv('GMAIL_OAUTH_SECRET')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    gmail_oauth_config = json.loads(get_secret(GMAIL_OAUTH_SECRET))
    logging.info(gmail_oauth_config['web']['token_uri'])

