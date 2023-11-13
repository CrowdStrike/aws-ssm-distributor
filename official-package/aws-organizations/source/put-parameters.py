"""
CrowdStrike Store Secret Parameters Lambda Function

______                         __ _______ __         __ __
|      |.----.-----.--.--.--.--|  |     __|  |_.----.|__|  |--.-----.
|   ---||   _|  _  |  |  |  |  _  |__     |   _|   _||  |    <|  -__|
|______||__| |_____|________|_____|_______|____|__|  |__|__|__|_____|

Falcon Store Secret Parameters Lambda Function v1.0

Creation date: 11.01.23 - ryanjpayne@CrowdStrike
"""

import boto3
import logging
import os
import requests
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FALCON_CLIENT_ID = os.environ['falcon_client_id']
FALCON_SECRET = os.environ['falcon_secret']
FALCON_CLOUD = os.environ['falcon_cloud']
FALCON_CLIENT_ID_NAME = os.environ['falcon_client_id_name']
FALCON_SECRET_NAME = os.environ['falcon_secret_name']
FALCON_CLOUD_NAME = os.environ['falcon_cloud_name']

SUCCESS = "SUCCESS"
FAILED = "FAILED"

def put_parameters(event):
    ssm = boto3.client('ssm')
    try:
        ssm.put_parameter(
            Name=FALCON_CLIENT_ID_NAME,
            Value=FALCON_CLIENT_ID,
            Type='SecureString',
            Overwrite=True,
            Tier='Standard',
            DataType='text'
        )
        ssm.put_parameter(
            Name=FALCON_SECRET_NAME,
            Value=FALCON_SECRET,
            Type='SecureString',
            Overwrite=True,
            Tier='Standard',
            DataType='text'
        )
        ssm.put_parameter(
            Name=FALCON_CLOUD_NAME,
            Value=FALCON_CLOUD,
            Type='SecureString',
            Overwrite=True,
            Tier='Standard',
            DataType='text'
        )
        parameter_names = [FALCON_CLIENT_ID_NAME, FALCON_SECRET_NAME, FALCON_CLOUD_NAME]
        return parameter_names
    except Exception as e:
        response_dict={}
        response_dict['exception'] = e
        cfnresponse_send(event, FAILED, response_dict, "CustomResourcePhysicalID")

def cfnresponse_send(event, responseStatus, responseData, physicalResourceId=None):
    responseUrl = event['ResponseURL']
    print(responseUrl)
    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = 'See the details in CloudWatch Log Stream: '
    responseBody['PhysicalResourceId'] = physicalResourceId
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']
    responseBody['Data'] = responseData
    json_responseBody = json.dumps(responseBody)
    print("Response body:\n" + json_responseBody)
    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }
    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))
    
def lambda_handler(event, context):
    logger.info('Got event {}'.format(event))
    logger.info('Context {}'.format(context))
    parameters = put_parameters()
    response_dict={}
    response_dict['parameters'] = parameters
    cfnresponse_send(event, SUCCESS, response_dict, "CustomResourcePhysicalID")
