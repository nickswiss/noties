import logging
import os
import boto3

from aws_utils.lambda_functions.http.decorators import rest_api
from aws_utils.lambda_functions.http.response import HTTPResponse

sqs = boto3.client("sqs")
SQS_QUEUE = os.getenv("SQS_ARN")
logger = logging.getLogger()


@rest_api
def lambda_handler(request):
    """SendGrid events webhook POST handler which accepts events
    and publishes to SQS
    """
    sqs.send_message(QueueUrl=SQS_QUEUE, MessageBody=request.body)
    logger.info(request.body)
    return HTTPResponse(data={'message': "Item queued."}, status=200)
