import json
import logging
import os

import boto3
import google.oauth2.credentials
from googleapiclient.discovery import build

from aws_utils.secrets_manager import get_secret

GMAIL_OAUTH_SECRET = os.getenv('GMAIL_OAUTH_SECRET')
AUTH_DB = os.getenv('AUTH_DB')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    gmail_oauth_config = json.loads(get_secret(GMAIL_OAUTH_SECRET))
    logging.info(gmail_oauth_config['web']['token_uri'])
    creds = boto3.resource('dynamodb').Table(AUTH_DB).get_item(Key={'email': 'nickarnold23@gmail.com'})['Item'][
        'credentials']
    credentials = google.oauth2.credentials.Credentials(
        **creds)
    gmail = build('gmail', 'v1', credentials=credentials)
    resp = gmail.users().watch(
        userId='me', body={'labelIds': ['INBOX'], 'topicName': 'projects/noties/topics/email'}).execute()
    logger.info(resp)
    gmail.close()
