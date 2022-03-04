import json
import logging
import os

import boto3
import google_auth_oauthlib.flow
import requests
from googleapiclient.discovery import build

from aws_utils.creds import credentials_to_dict
from aws_utils.lambda_functions.http.decorators import rest_api
from aws_utils.lambda_functions.http.response import HTTPResponse
from aws_utils.secrets_manager import get_secret
from email_utils import OAUTH_SCOPES
from email_utils.models import EmailHistory

GMAIL_OAUTH_SECRET = os.getenv('GMAIL_OAUTH_SECRET')
DOMAIN_NAME = os.getenv('DOMAIN_NAME')
AUTH_DB = os.getenv('AUTH_DB')
EMAIL_DB = os.getenv('EMAIL_DB')

OAUTH_SUCCESS = os.path.join(os.path.dirname(__file__), "oauth_success.html")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

tmp_file = '/tmp/oauth.json'


def oauth_success():
    with open(OAUTH_SUCCESS, "r") as f:
        template = f.read()
    return template


@rest_api
def lambda_handler(request):
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    gmail_oauth_config = json.loads(get_secret(GMAIL_OAUTH_SECRET))
    logger.info(request._event)
    logger.info(request._context)
    state = request.query_string_params['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        gmail_oauth_config,
        scopes=OAUTH_SCOPES,
        state=state
    )

    flow.redirect_uri = f'https://{DOMAIN_NAME}/callback'

    logger.info(flow.redirect_uri)

    flow.fetch_token(code=request.query_string_params['code'])

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    email = get_user_email(credentials.token)['email']
    boto3.resource('dynamodb').Table(AUTH_DB).put_item(Item=credentials_to_dict(email, credentials))

    gmail = build('gmail', 'v1', credentials=credentials)
    resp = gmail.users().watch(
        userId='me',
        body={'labelIds': ['INBOX'], 'topicName': 'projects/noties/topics/email'}
    ).execute()

    boto3.resource('dynamodb').Table(EMAIL_DB).put_item(
        Item=EmailHistory(
            email=email,
            watch_expiration=int(int(resp['expiration']) / 1000)
        ).dict())
    return HTTPResponse(
        data=oauth_success(),
        headers={'Content-Type': 'text/html'},
    )


def get_user_email(access_token):
    r = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        params={'access_token': access_token})
    return r.json()
