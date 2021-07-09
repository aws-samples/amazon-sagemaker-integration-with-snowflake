import json
import boto3
import os
import time
import logging
from botocore.exceptions import ClientError
import requests

import snowflake.connector

SUCCESS = 'SUCCESS'
FAILED = 'FAILED'
EMPTY_RESPONSE_DATA = {}

EXTERNAL_ID = "external_id"
SERVICE = "service"
USER_ARN = "user_arn"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    # Get variables from os
    api_gateway_url = os.environ['ApiGatewayURL']
    api_gateway_role_arn = os.environ['ApiGatewayRoleARN']
    api_gateway_role_name = os.environ['ApiGatewayRoleName']
    auto_ml_role_arn = os.environ['AutoMLRoleARN']
    auto_ml_role_name = os.environ['AutoMLRoleName']
    region_name = os.environ['Region']
    s3_bucket_name = os.environ['S3BucketName']
    secret_name = os.environ['SecretArn']
    snowflake_role_name = os.environ['SnowflakeRole']
    stack_name = os.environ['StackName']

    logger.info("api_gateway_role_arn: " + api_gateway_role_arn)
    logger.info("api_gateway_role_name: " + api_gateway_role_name)
    logger.info("auto_ml_role_arn: " + auto_ml_role_arn)
    logger.info("auto_ml_role_name: " + auto_ml_role_name)
    logger.info("s3_bucket_name: " + s3_bucket_name)
    logger.info("region_name: " + region_name)
    logger.info("secret_name: " + secret_name)
    logger.info("snowflake_role_name: " + snowflake_role_name)

    # Initialize integration related variables
    storage_integration_info = {}
    api_integration_info = {}

    # Delete
    if event['RequestType'] == 'Delete':
        sendResponse(event, context, SUCCESS, EMPTY_RESPONSE_DATA)
        return

    # Get the information connection from Secrets Manager
    try:
        get_secret_value_response = get_secret_information(region_name, secret_name)
    except:
        sendResponse(event, context, FAILED, EMPTY_RESPONSE_DATA)
        return

    # Decrypted secret using the associated KMS CMK
    # Ensure the Secret is in String mode
    if 'SecretString' not in get_secret_value_response:
        logger.error("The Secret is not in String mode")
        sendResponse(event, context, FAILED, EMPTY_RESPONSE_DATA)
        return

    # Create Snowflake resource
    try:
        snowflake_connection = connect_to_snowflake(get_secret_value_response, snowflake_role_name)
        snowflake_cursor = snowflake_connection.cursor()

        snowflake_resources_prefix = stack_name + "_" + region_name
        storage_integration_name = snowflake_resources_prefix + "_storage_integration"
        api_integration_name = snowflake_resources_prefix + "_api_integration"

        # Create Snowflake Integrations
        create_storage_integration(snowflake_cursor, storage_integration_name, auto_ml_role_arn, s3_bucket_name)
        create_api_integration(snowflake_cursor, api_integration_name, api_gateway_role_arn, api_gateway_url)

        # Describe Snowflake integrations
        storage_integration_info = get_storage_integration_info_for_policy(snowflake_cursor, storage_integration_name)
        api_integration_info = get_api_integration_info_for_policy(snowflake_cursor, api_integration_name)
    except Exception as e:
        logger.exception('Problem running SQL statements: ' + str(e))
        responseData = {'Failed': 'Unable to execute SQL statements in Snowflake'}
        sendResponse(event, context, FAILED, responseData)
        return
    finally:
        if 'snowflake_cursor' in vars():
            snowflake_cursor.close()
        if 'snowflake_connection' in vars():
            snowflake_connection.close()

    # Update IAM role to add Snowflake information
    logger.info("Updating IAM Role")
    storage_integration_policy_str = create_policy_string(storage_integration_info)
    api_integration_policy_str = create_policy_string(api_integration_info)

    try:
        update_assume_role_policy(storage_integration_policy_str, auto_ml_role_name)
        update_assume_role_policy(api_integration_policy_str, api_gateway_role_name)
    except Exception as e:
        logger.exception('Problem updating assume role policy: ' + str(e))
        responseData = {'Failed': 'There was a problem updating the assume role policies'}
        sendResponse(event, context, FAILED, responseData)
        return

    responseData = {'Success': 'Snowflake resources created.'}
    sendResponse(event, context, SUCCESS, responseData)
    logger.info("Success")

def get_secret_information(region_name, secret_name):
    logger.info("Getting secret information")
    try:
        secretsmanager = boto3.client('secretsmanager')

        return secretsmanager.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.exception("The requested secret " + secret_name + " was not found")
        else:
            logger.exception(e)
        raise e

def connect_to_snowflake(get_secret_value_response, snowflake_role_name):
    secret_string = get_secret_value_response['SecretString']

    secret = json.loads(secret_string)
    snowflake_account = secret['accountid']
    snowflake_password = secret['password']
    snowflake_userName = secret['username']

    # Connect to Snowflake
    logger.info("Connecting to Snowflake")
    snowflake_connection = snowflake.connector.connect(
        user=snowflake_userName,
        password=snowflake_password,
        account=snowflake_account,
        role=snowflake_role_name
    )

    return snowflake_connection

def sendResponse(event, context, responseStatus, responseData):
    responseBody = {'Status': responseStatus,
                    'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
                    'PhysicalResourceId': context.log_stream_name,
                    'StackId': event['StackId'],
                    'RequestId': event['RequestId'],
                    'LogicalResourceId': event['LogicalResourceId'],
                    'Data': responseData}
    req = requests.put(event['ResponseURL'], data=json.dumps(responseBody))
    if req.status_code != 200:
        raise Exception('Received a non-200 HTTP response while sending response to CloudFormation.')
    return

def create_storage_integration(snowflake_cursor, storage_integration_name, auto_ml_role_arn, s3_bucket_name):
    logger.info("Creating Storage Integration")

    storage_integration_str = ("create or replace storage integration \"%s\" \
    type = external_stage \
    storage_provider = s3 \
    enabled = true \
    storage_aws_role_arn = '%s' \
    storage_allowed_locations = ('s3://%s')") % (storage_integration_name, auto_ml_role_arn, s3_bucket_name)

    snowflake_cursor.execute(storage_integration_str)

def create_api_integration(snowflake_cursor, api_integration_name, api_gateway_role_arn, api_gateway_url):
    logger.info("Creating API Integration")

    api_integration_str = ("create or replace api integration \"%s\" \
    api_provider = aws_api_gateway \
    api_aws_role_arn = '%s' \
    api_allowed_prefixes = ('%s') \
    enabled = true \
    ") % (api_integration_name, api_gateway_role_arn, api_gateway_url)

    snowflake_cursor.execute(api_integration_str)


def get_storage_integration_info_for_policy(snowflake_cursor, storage_integration_name):
    logger.info("Describing Storage Integration")
    storage_user_arn = ''
    storage_external_id = ''

    snowflake_cursor.execute(("describe integration \"%s\"") % (storage_integration_name))
    rows = snowflake_cursor.fetchall()
    for row in rows:
        value = list(row)
        if (value[0] == "STORAGE_AWS_IAM_USER_ARN"):
            storage_user_arn = value[2]
        if (value[0] == "STORAGE_AWS_EXTERNAL_ID"):
            storage_external_id = value[2]
    return {
        SERVICE: "sagemaker.amazonaws.com",
        USER_ARN: storage_user_arn,
        EXTERNAL_ID: storage_external_id
    }

def get_api_integration_info_for_policy(snowflake_cursor, api_integration_name):
    logger.info("Describing API Integration")
    storage_user_arn = ''
    storage_external_id = ''

    snowflake_cursor.execute(("describe integration \"%s\"") % (api_integration_name))
    rows = snowflake_cursor.fetchall()
    for row in rows:
        value = list(row)
        if (value[0] == "API_AWS_IAM_USER_ARN"):
            api_user_arn = value[2]
        if (value[0] == "API_AWS_EXTERNAL_ID"):
            api_external_id = value[2]
    return {
        SERVICE: "apigateway.amazonaws.com",
        USER_ARN: api_user_arn,
        EXTERNAL_ID: api_external_id
    }

def create_policy_string(integration_info):
    policy_json = {
      "Version": "2012-10-17",
      "Statement":[
        {
          "Effect": "Allow",
          "Principal": {"Service":[integration_info[SERVICE]]},
          "Action": "sts:AssumeRole"
        },
        {
          "Effect": "Allow",
          "Principal": {
            "AWS":[integration_info[USER_ARN]]
          },
          "Action": "sts:AssumeRole",
          "Condition": {
            "StringEquals": {
              "sts:ExternalId": integration_info[EXTERNAL_ID]
            }
          }
        }
      ]
    }
    return json.dumps(policy_json)

def update_assume_role_policy(policy_str, role_name):
    logger.info('Updating assume role policy for role: ' + role_name)
    logger.info('Policy used: ' + policy_str)
    iam = boto3.client('iam')
    storage_response = iam.update_assume_role_policy(
        PolicyDocument=policy_str,
        RoleName=role_name
    )
