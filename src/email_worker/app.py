import json
import logging
import os
import re
from twilio.rest import Client
import datetime
import httplib2

import boto3
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient import errors as google_api_errors


from aws_utils.creds import credentials_to_dict
from aws_utils.secrets_manager import get_secret
from email_utils.models import EmailHistory, Email

AUTH_DB = os.getenv('AUTH_DB')
EMAIL_DB = os.getenv('EMAIL_DB')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FROM_HEADER_NAME = 'From'
SUBJECT_HEADER_NAME = 'Subject'
USEFUL_HEADERS = ['Subject', 'From']

EMAIL = 'nickarnold23@gmail.com'


def scrape_email_data(message_data):
    scraped_data = list(
        filter(
            lambda header: header.get('name') in USEFUL_HEADERS if isinstance(header, dict) else False,
            message_data['headers']
        )
    )
    from_address_full = list(filter(lambda d: d.get('name') == FROM_HEADER_NAME, scraped_data))[0]['value']

    try:
        from_address = re.search(' <(.*)>', from_address_full).group(1).lower()
    except AttributeError:  # no group means no match, which means no readble name, just email
        from_address = from_address_full.lower()

    try:
        subject_line = list(filter(lambda d: d.get('name') == SUBJECT_HEADER_NAME, scraped_data))[0]['value'].lower()
    except:
        subject_line = 'no subject'

    email_data = {
        'from_address': from_address,  # from address
        'from_address_full': from_address_full,  # includes readable name, i.e. 'Pocket <noreply@getpocket.com>'
        'subject_line': subject_line
    }
    return email_data


def get_email_message_data(gmail_client, message_id):
    emails = []
    try:
        message_data = gmail_client.users().messages().get(userId='me', id=message_id).execute()['payload']
        emails += [scrape_email_data(message_data)]
    except google_api_errors.HttpError:
        messages = gmail_client.users().threads().get(userId='me', id=message_id).execute()['messages']
        for message in messages:
            logger.info(message)
            email_data = scrape_email_data(message['payload'])
            emails += [email_data]
    return emails


def update_watch_if_expired(gmail_client, email_history: EmailHistory):
    expiration_date = datetime.datetime.fromtimestamp(email_history.watch_expiration)
    if expiration_date < (datetime.datetime.now() + datetime.timedelta(hours=12)):   # expires within 6 hours, assuming that some form of activity will happen in inbox within time frame
        resp = gmail_client.users().watch(
            userId='me',
            body={'labelIds': ['INBOX'], 'topicName': 'projects/noties/topics/email'}
        ).execute()
        email_history.watch_expiration = int(int(resp['expiration'])/1000)
        logger.info(f'Expiration updated: {email_history.watch_expiration}')



def lambda_handler(event, context):
    twilio_creds = json.loads(get_secret("noties/twilio"))
    twilio_key = twilio_creds['key']
    twilio_sid = twilio_creds['sid']
    twilio_notify_number = twilio_creds['notify_number']
    db_creds = boto3.resource('dynamodb').Table(AUTH_DB).get_item(
        Key={'email': EMAIL}
    )['Item']['credentials']
    credentials = Credentials(**db_creds)
    print(credentials.to_json())
    logger.info('Credentials refreshed here 1')
    if not credentials.valid:
        request = httplib2.Http()
        credentials.refresh(request)
        print(credentials.to_json())
        logger.info('Credentials refreshed.')
        boto3.resource('dynamodb').Table(AUTH_DB).put_item(
            Item=credentials_to_dict(EMAIL, credentials)
        )

    gmail = build('gmail', 'v1', credentials=credentials)
    logger.info(event)
    message = json.loads(event['Records'][0]['body'])

    history = gmail.users().history().list(
        userId='me',
        startHistoryId=message['historyId'],
        historyTypes='messageAdded'
    ).execute()
    import pdb ; pdb.set_trace()
    if not history.get('history'):
        logger.info('No history for event')
        return

    history_events = history['history']
    emails = []
    for history_event in history_events:
        for message in history_event['messages']:  # short list, normally of length 1
            message_id = message['id']
            email_data = get_email_message_data(gmail, message_id)
            emails += email_data

    new_emails = [Email(**email) for email in emails]
    try:
        email_data = boto3.resource('dynamodb').Table(EMAIL_DB).get_item(
            Key={'email': EMAIL}
        )['Item']
        email_history = EmailHistory(**email_data)

    except KeyError:
        email_history = EmailHistory(
            email=EMAIL
        )

    email_history.emails += new_emails
    logger.info([email.dict() for email in new_emails])
    email_history.emails = email_history.emails[-100:]   # only hold on to last 100 emails in history

    update_watch_if_expired(gmail, email_history)

    boto3.resource('dynamodb').Table(EMAIL_DB).put_item(
        Item=email_history.dict()
    )

    notify_emails = set(email_history.notify_from_addresses)

    for email in new_emails:
        if email.from_address in notify_emails:
            notify_twilio(email, twilio_notify_number, twilio_key, twilio_sid)


def notify_twilio(email: Email, number, token, sid):

    client = Client(sid, token)

    message = client.messages.create(
        to=number,
        body=f'New email alert \nFrom Address: {email.from_address_full} \nSubject: {email.subject_line}',
        from_='+18646894488'
    )

    logger.info(f'{message.sid} alerted.')
