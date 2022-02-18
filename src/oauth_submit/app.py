import json
import logging
import os

import google_auth_oauthlib.flow

from aws_utils.lambda_functions.http.decorators import rest_api
from aws_utils.lambda_functions.http.response import HTTPResponse
from aws_utils.secrets_manager import get_secret

GMAIL_OAUTH_SECRET = os.getenv('GMAIL_OAUTH_SECRET')
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]
DOMAIN_NAME = os.getenv('DOMAIN_NAME')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@rest_api
def lambda_handler(request):
    gmail_oauth_config = json.loads(get_secret(GMAIL_OAUTH_SECRET))

    # Use the client_secret.json file to identify the application requesting
    # authorization. The client ID (from that file) and access scopes are required.
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        gmail_oauth_config,
        scopes=SCOPES
    )

    # Indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required. The value must exactly
    # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
    # configured in the API Console. If this value doesn't match an authorized URI,
    # you will get a 'redirect_uri_mismatch' error.
    flow.redirect_uri = f'https://{DOMAIN_NAME}/callback'

    # Generate URL for request to Google's OAuth 2.0 server.
    # Use kwargs to set optional request parameters.
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true'
    )
    logger.info(state)
    return HTTPResponse(
        data=None,
        headers={'Content-Type': 'text/html', 'Location': authorization_url},
        status=302
    )
