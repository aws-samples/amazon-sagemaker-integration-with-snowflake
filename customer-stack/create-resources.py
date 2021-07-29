import json
import boto3
import os
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
    kms_key_arn = os.environ['KmsKeyArn']
    snowflake_role_name = os.environ['SnowflakeRole']
    stack_name = os.environ['StackName']
    database_name = os.environ['DatabaseName']
    schema_name = os.environ['SchemaName']

    logger.info("api_gateway_url: " + api_gateway_url)
    logger.info("api_gateway_role_arn: " + api_gateway_role_arn)
    logger.info("api_gateway_role_name: " + api_gateway_role_name)
    logger.info("auto_ml_role_arn: " + auto_ml_role_arn)
    logger.info("auto_ml_role_name: " + auto_ml_role_name)
    logger.info("region_name: " + region_name)
    logger.info("s3_bucket_name: " + s3_bucket_name)
    logger.info("secret_name: " + secret_name)
    logger.info("kms_key_arn: " + kms_key_arn)
    logger.info("snowflake_role_name: " + snowflake_role_name)
    logger.info("stack_name: " + stack_name)
    logger.info("database_name: " + database_name)
    logger.info("schema_name: " + schema_name)

    # Delete
    if event['RequestType'] == 'Delete':
        logger.info("No action for Delete. Exiting.")
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

        snowflake_cursor.execute(("use database %s;") % (database_name))
        
        snowflake_cursor.execute(("use schema %s;") % (schema_name))

        storage_integration_name = "AWS_AUTOPILOT_STORAGE_INTEGRATION" + "_" + stack_name
        api_integration_name = "AWS_AUTOPILOT_API_INTEGRATION" + "_" + stack_name

        # Create Snowflake Integrations
        create_storage_integration(snowflake_cursor, storage_integration_name, auto_ml_role_arn, s3_bucket_name)
        create_api_integration(snowflake_cursor, api_integration_name, api_gateway_role_arn, api_gateway_url)
        create_external_functions(snowflake_cursor, api_integration_name, auto_ml_role_arn, api_gateway_url, s3_bucket_name, secret_name, storage_integration_name, snowflake_role_name, kms_key_arn)

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
    logger.info("Creating Storage Integration [storage_integration_name=%s, auto_ml_role_arn=%s, s3_bucket_name=%s]",
                storage_integration_name, auto_ml_role_arn, s3_bucket_name)

    storage_integration_str = ("create or replace storage integration \"%s\" \
    type = external_stage \
    storage_provider = s3 \
    enabled = true \
    storage_aws_role_arn = '%s' \
    storage_allowed_locations = ('s3://%s')") % (storage_integration_name, auto_ml_role_arn, s3_bucket_name)

    snowflake_cursor.execute(storage_integration_str)

def create_api_integration(snowflake_cursor, api_integration_name, api_gateway_role_arn, api_gateway_url):
    logger.info("Creating API Integration [api_integration_name=%s, api_gateway_role_arn=%s, api_gateway_url=%s]",
                api_integration_name, api_gateway_role_arn, api_gateway_url)

    api_integration_str = ("create or replace api integration \"%s\" \
    api_provider = aws_api_gateway \
    api_aws_role_arn = '%s' \
    api_allowed_prefixes = ('%s') \
    enabled = true \
    ") % (api_integration_name, api_gateway_role_arn, api_gateway_url)

    snowflake_cursor.execute(api_integration_str)


def create_external_functions(snowflake_cursor, api_integration_name, auto_ml_role_arn, api_gateway_url, s3_bucket_name, secret_arn, storage_integration_name, snowflake_role_name, kms_key_arn):
    create_describemodel_ef(snowflake_cursor, api_integration_name, api_gateway_url)
    create_createendpoint_ef(snowflake_cursor, api_integration_name, api_gateway_url)
    create_createendpointconfig_ef(snowflake_cursor, api_integration_name, api_gateway_url)
    create_describeendpoint_ef(snowflake_cursor, api_integration_name, api_gateway_url)
    create_deleteendpoint_ef(snowflake_cursor, api_integration_name, api_gateway_url)
    create_predictoutcome_ef(snowflake_cursor, api_integration_name, api_gateway_url)
    create_createmodel_ef(snowflake_cursor, api_integration_name, api_gateway_url, secret_arn, s3_bucket_name, storage_integration_name, auto_ml_role_arn, snowflake_role_name, kms_key_arn)
    create_deleteendpointconfig_ef(snowflake_cursor, api_integration_name, api_gateway_url)
    create_describeendpointconfig_ef(snowflake_cursor, api_integration_name, api_gateway_url)


def create_describemodel_ef(snowflake_cursor, api_integration_name, api_gateway_url):
    logger.info("Creating External function: AWS_AUTOPILOT_DESCRIBE_MODEL [api_integration_name=%s, api_gateway_url=%s]", api_integration_name, api_gateway_url)

    describemodel_serializer_str = ("create or replace function AWS_AUTOPILOT_DESCRIBE_MODEL_SERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let item = EVENT.body.data[0][1]; \
        let payload = { \
            \"AutoMLJobName\" : item + \"-job\" \
        }; \
        return {\"body\": JSON.stringify(payload)};\
        $$")

    snowflake_cursor.execute(describemodel_serializer_str)

    describemodel_deserializer_str = ("create or replace function AWS_AUTOPILOT_DESCRIBE_MODEL_DESERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let responseBody = EVENT.body; \
        let response ={}; \
        response[\"JobStatus\"] = responseBody.AutoMLJobStatus; \
        response[\"JobStatusDetails\"] = responseBody.AutoMLJobSecondaryStatus; \
        if (responseBody.AutoMLJobStatus === \"Completed\") \
        { \
        response[\"ObjectiveMetric\"] = responseBody.BestCandidate.FinalAutoMLJobObjectiveMetric.MetricName; \
        response[\"BestObjectiveMetric\"] = responseBody.BestCandidate.FinalAutoMLJobObjectiveMetric.Value; \
        } else if (responseBody.AutoMLJobStatus === \"Failed\") \
        {\
            response[\"FailureReason\"] = responseBody.FailureReason;\
        }\
        \
        response[\"PartialFailureReasons\"] = responseBody.PartialFailureReasons;\
        response[\"AutoMLJobSecondaryStatus\"] = responseBody.AutoMLJobSecondaryStatus;\
        \
        return {\"body\":{   \"data\" : [[0,response]]  }};\
        $$;")

    snowflake_cursor.execute(describemodel_deserializer_str)

    create_describemodel_ef_str = ("create or replace external function AWS_AUTOPILOT_DESCRIBE_MODEL(modelname varchar) \
        returns variant \
        api_integration = \"%s\" \
        serializer = AWS_AUTOPILOT_DESCRIBE_MODEL_SERIALIZER \
        deserializer=AWS_AUTOPILOT_DESCRIBE_MODEL_DESERIALIZER \
        max_batch_rows=1 \
        as '%s/describemodel';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_describemodel_ef_str)


def create_createendpoint_ef(snowflake_cursor, api_integration_name, api_gateway_url):
    logger.info("Creating External function: AWS_AUTOPILOT_CREATE_ENDPOINT [api_integration_name=%s, api_gateway_url=%s]", api_integration_name, api_gateway_url)

    createendpoint_serializer_str = ("create or replace function AWS_AUTOPILOT_CREATE_ENDPOINT_SERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let endpointName = EVENT.body.data[0][1]; \
        let endpointConfigName = EVENT.body.data[0][2]; \
        let payload = { \
                \"EndpointName\" : endpointName, \
                \"EndpointConfigName\" : endpointConfigName, \
                \"DeletionCondition\": { \
                \"MaxRuntimeInSeconds\": 7200 \
                } \
              }; \
        return {\"body\": payload}; \
        $$")

    snowflake_cursor.execute(createendpoint_serializer_str)

    createendpoint_deserializer_str = ("create or replace function AWS_AUTOPILOT_CREATE_ENDPOINT_DESERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
            return {\"body\": {   \"data\" : [[0, EVENT.body]]  }}\
        $$;")

    snowflake_cursor.execute(createendpoint_deserializer_str)

    create_createendpoint_ef_str = ("create or replace external function AWS_AUTOPILOT_CREATE_ENDPOINT(endpointName varchar, endpointConfigName varchar) \
    returns variant \
    api_integration = \"%s\" \
    serializer = AWS_AUTOPILOT_CREATE_ENDPOINT_SERIALIZER \
    deserializer=AWS_AUTOPILOT_CREATE_ENDPOINT_DESERIALIZER \
    max_batch_rows=1 \
    as '%s/createendpoint';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_createendpoint_ef_str)


def create_createendpointconfig_ef(snowflake_cursor, api_integration_name, api_gateway_url):
    logger.info("Creating External function: AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG [api_integration_name=%s, api_gateway_url=%s]", api_integration_name, api_gateway_url)

    createendpointconfig_serializer_str = ("create or replace function AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG_SERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let endpointConfigName = EVENT.body.data[0][1]; \
        let modelName = EVENT.body.data[0][2]; \
        let instanceType = EVENT.body.data[0][3]; \
        let instanceCount = EVENT.body.data[0][4]; \
        let payload = { \
        \"EndpointConfigName\": endpointConfigName, \
        \"ProductionVariants\" : [ \
        { \
            \"InstanceType\": instanceType, \
            \"ModelName\": modelName + \"-job-best-model\", \
            \"InitialInstanceCount\": instanceCount, \
            \"VariantName\" : \"AllTrafficVariant\" \
        }] \
        }; \
        return {\"body\": payload}; \
        $$")

    snowflake_cursor.execute(createendpointconfig_serializer_str)

    createendpointconfig_deserializer_str = ("create or replace function AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG_DESERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
            return {\"body\": {   \"data\" : [[0, EVENT.body]]  }};\
        $$;")

    snowflake_cursor.execute(createendpointconfig_deserializer_str)

    create_createendpointconfig_ef_str = ("create or replace external function AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG(endpointConfigName varchar, modelName varchar, instanceType varchar, instanceCount int) \
    returns variant \
    api_integration = \"%s\" \
    serializer = AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG_SERIALIZER \
    deserializer=AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG_DESERIALIZER \
    max_batch_rows=1 \
    as '%s/createendpointconfig';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_createendpointconfig_ef_str)

def create_describeendpointconfig_ef(snowflake_cursor, api_integration_name, api_gateway_url):
    logger.info("Creating External function: AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG [api_integration_name=%s, api_gateway_url=%s]", api_integration_name, api_gateway_url)

    describeendpointconfig_serializer_str = ("create or replace function AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG_SERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let endpointConfigName = EVENT.body.data[0][1]; \
        let payload = { \
        \"EndpointConfigName\": endpointConfigName \
        }; \
        return {\"body\": payload}; \
        $$")

    snowflake_cursor.execute(describeendpointconfig_serializer_str)

    describeendpointconfig_deserializer_str = ("create or replace function AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG_DESERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
            return {\"body\": {   \"data\" : [[0, EVENT.body]]  }};\
        $$;")

    snowflake_cursor.execute(describeendpointconfig_deserializer_str)

    create_describeendpointconfig_ef_str = ("create or replace external function AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG(endpointConfigName varchar, modelName varchar, instanceType varchar, instanceCount int) \
    returns variant \
    api_integration = \"%s\" \
    serializer = AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG_SERIALIZER \
    deserializer=AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG_DESERIALIZER \
    max_batch_rows=1 \
    as '%s/describeendpointconfig';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_describeendpointconfig_ef_str)

def create_deleteendpointconfig_ef(snowflake_cursor, api_integration_name, api_gateway_url):
    logger.info("Creating External function: AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG [api_integration_name=%s, api_gateway_url=%s]", api_integration_name, api_gateway_url)

    deleteendpointconfig_serializer_str = ("create or replace function AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG_SERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let endpointConfigName = EVENT.body.data[0][1]; \
        let payload = { \
        \"EndpointConfigName\": endpointConfigName \
        }; \
        return {\"body\": payload}; \
        $$")

    snowflake_cursor.execute(deleteendpointconfig_serializer_str)

    deleteendpointconfig_deserializer_str = ("create or replace function AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG_DESERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
            return {\"body\": {   \"data\" : [[0, EVENT.body]]  }};\
        $$;")

    snowflake_cursor.execute(deleteendpointconfig_deserializer_str)

    create_deleteendpointconfig_ef_str = ("create or replace external function AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG(endpointConfigName varchar, modelName varchar, instanceType varchar, instanceCount int) \
    returns variant \
    api_integration = \"%s\" \
    serializer = AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG_SERIALIZER \
    deserializer=AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG_DESERIALIZER \
    max_batch_rows=1 \
    as '%s/deleteendpointconfig';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_deleteendpointconfig_ef_str)

def create_describeendpoint_ef(snowflake_cursor, api_integration_name, api_gateway_url):
    logger.info("Creating External function: AWS_AUTOPILOT_DESCRIBE_ENDPOINT [api_integration_name=%s, api_gateway_url=%s]", api_integration_name, api_gateway_url)

    describeendpoint_serializer_str = ("create or replace function AWS_AUTOPILOT_DESCRIBE_ENDPOINT_SERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
            let endpointName = EVENT.body.data[0][1]; \
            let payload = { \
                \"EndpointName\" : endpointName \
              }; \
        return {\"body\": JSON.stringify(payload)};\
        $$")

    snowflake_cursor.execute(describeendpoint_serializer_str)

    describeendpoint_deserializer_str = ("create or replace function AWS_AUTOPILOT_DESCRIBE_ENDPOINT_DESERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
            return {\"body\": {   \"data\" : [[0, EVENT.body]]  }}\
        $$;")

    snowflake_cursor.execute(describeendpoint_deserializer_str)

    create_describeendpoint_ef_str = ("create or replace external function AWS_AUTOPILOT_DESCRIBE_ENDPOINT(endpointName varchar) \
    returns variant \
    api_integration = \"%s\" \
    serializer = AWS_AUTOPILOT_DESCRIBE_ENDPOINT_SERIALIZER \
    deserializer=AWS_AUTOPILOT_DESCRIBE_ENDPOINT_DESERIALIZER \
    max_batch_rows=1 \
    as '%s/describeendpoint';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_describeendpoint_ef_str)


def create_deleteendpoint_ef(snowflake_cursor, api_integration_name, api_gateway_url):
    logger.info("Creating External function: AWS_AUTOPILOT_DELETE_ENDPOINT [api_integration_name=%s, api_gateway_url=%s]", api_integration_name, api_gateway_url)

    deleteendpoint_serializer_str = ("create or replace function AWS_AUTOPILOT_DELETE_ENDPOINT_SERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
            let endpointName = EVENT.body.data[0][1]; \
            let payload = { \
                \"EndpointName\" : endpointName \
              }; \
        return {\"body\": JSON.stringify(payload)};\
        $$")

    snowflake_cursor.execute(deleteendpoint_serializer_str)

    deleteendpoint_deserializer_str = ("create or replace function AWS_AUTOPILOT_DELETE_ENDPOINT_DESERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
            return {\"body\": {   \"data\" : [[0, EVENT.body]]  }}\
        $$;")

    snowflake_cursor.execute(deleteendpoint_deserializer_str)

    create_deleteendpoint_ef_str = ("create or replace external function AWS_AUTOPILOT_DELETE_ENDPOINT(endpointName varchar) \
    returns variant \
    api_integration = \"%s\" \
    serializer = AWS_AUTOPILOT_DELETE_ENDPOINT_SERIALIZER \
    deserializer=AWS_AUTOPILOT_DELETE_ENDPOINT_DESERIALIZER \
    max_batch_rows=1 \
    as '%s/deleteendpoint';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_deleteendpoint_ef_str)


def create_predictoutcome_ef(snowflake_cursor, api_integration_name, api_gateway_url):
    logger.info("Creating External function: AWS_AUTOPILOT_PREDICT_OUTCOME [api_integration_name=%s, api_gateway_url=%s]", api_integration_name, api_gateway_url)

    predictoutcome_serializer_str = ("create or replace function AWS_AUTOPILOT_PREDICT_OUTCOME_SERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let modelName = \"/\"  + EVENT.body.data[0][1]; \
        var payload = []; \
        for(i = 0; i < EVENT.body.data.length; i++) { \
            var row = EVENT.body.data[i]; \
            payload[i] = row[2]; \
        } \
        payloadBody = payload.map(e => e.join(',')).join('\\n'); \
        return {\"body\": payloadBody,  \"urlSuffix\" : modelName}; \
        $$")

    snowflake_cursor.execute(predictoutcome_serializer_str)

    predictoutcome_deserializer_str = ("create or replace function AWS_AUTOPILOT_PREDICT_OUTCOME_DESERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let array_of_rows_to_return = []; \
        let rows = EVENT.body.predictions; \
        for (let i = 0; i < rows.length; i++) { \
        let row_to_return = [i, rows[i]]; \
        array_of_rows_to_return.push(row_to_return); \
        } \
        return {\"body\": {\"data\": array_of_rows_to_return}}; \
        $$;")

    snowflake_cursor.execute(predictoutcome_deserializer_str)

    create_predictoutcome_ef_str = ("create or replace external function AWS_AUTOPILOT_PREDICT_OUTCOME(endpointName varchar, columns array) \
    returns variant \
    api_integration = \"%s\" \
    serializer = AWS_AUTOPILOT_PREDICT_OUTCOME_SERIALIZER \
    deserializer=AWS_AUTOPILOT_PREDICT_OUTCOME_DESERIALIZER \
    max_batch_rows=1 \
    as '%s/predictoutcome';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_predictoutcome_ef_str)


def create_createmodel_ef(snowflake_cursor, api_integration_name, api_gateway_url, secret_arn, s3_bucket_name, storage_integration_name, auto_ml_role_arn, snowflake_role_name, kms_key_arn):
    logger.info(
        "Creating External function: AWS_AUTOPILOT_CREATE_MODEL [api_integration_name=%s, api_gateway_url=%s, secret_arn=%s, s3_bucket_name=%s, storage_integration_name=%s, auto_ml_role_arn=%s, snowflake_role_name=%s, kms_key_arn=%s]",
        api_integration_name, api_gateway_url, secret_arn, s3_bucket_name, storage_integration_name, auto_ml_role_arn,
        snowflake_role_name, kms_key_arn)

    createmodel_serializer_str = ("create or replace function AWS_AUTOPILOT_CREATE_MODEL_SERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let modelname = EVENT.body.data[0][1]; \
        let targetTable = EVENT.body.data[0][2]; \
        let targetCol = EVENT.body.data[0][3]; \
        let maxRunningTime = 7200; \
        let deployModel = true; /* TODO: Unused for now */ \
        let modelEndpointTTL = 7*24*60*60; \
        let problemType; \
        let objectiveMetric; \
        \
        if (EVENT.body.data[0].length == 9) { \
            if (EVENT.body.data[0][4] != undefined) { \
                objectiveMetric = EVENT.body.data[0][4]; \
            } \
            \
            if (EVENT.body.data[0][5] != undefined) { \
                problemType = EVENT.body.data[0][5]; \
            } \
            \
            if (EVENT.body.data[0][6] != undefined) { \
                maxRunningTime = EVENT.body.data[0][6]; \
            } \
            \
            if (EVENT.body.data[0][7] != undefined) { \
                deployModel = EVENT.body.data[0][7]; \
            } \
            \
            if (EVENT.body.data[0][8] != undefined) { \
                modelEndpointTTL = EVENT.body.data[0][8]; \
            } \
        } \
        \
        let contextHeaders = EVENT.contextHeaders; \
        let jobDatasetsPath = modelname + \"-job/datasets/\" ; \
        let databaseName = contextHeaders[\"sf-context-current-database\"]; \
        let schemaName = contextHeaders[\"sf-context-current-schema\"]; \
        let tableNameComponents = targetTable.split(\".\"); \
        let s3OutputUri = \"s3://%s/output/\"; \
        let kmsKeyArn = \"%s\"; \
        if (tableNameComponents.length === 3) \
        {\
            databaseName = tableNameComponents[0]; \
            schemaName = tableNameComponents[1]; \
        } else if (tableNameComponents.length === 2) \
        { \
            schemaName = tableNameComponents[0];\
        }\
        \
        let payload = { \
            \"AutoMLJobConfig\": { \
            \"CompletionCriteria\": { \
                \"MaxAutoMLJobRuntimeInSeconds\": maxRunningTime \
            } \
            }, \
            \"AutoMLJobName\": modelname + \"-job\", \
            \"ModelDeployConfig\": { \
                \"ModelDeployMode\": \"Endpoint\",\
                \"EndpointConfigDefinitions\": [\
                {\
                    \"EndpointConfigName\":  modelname + \"-m5-4xl-2\",\
                    \"InitialInstanceCount\": 2,\
                    \"InstanceType\": \"ml.m5.4xlarge\"\
                }\
                ],\
                \"EndpointDefinitions\": [\
                {\
                    \"EndpointName\": modelname,\
                    \"EndpointConfigName\": modelname + \"-m5-4xl-2\",\
                    \"DeletionCondition\": {\
                    \"MaxRuntimeInSeconds\": modelEndpointTTL\
                    }\
                }\
                ]\
            },\
            \"InputDataConfig\": [\
            {\
                \"TargetAttributeName\": targetCol.toUpperCase(),\
                \"AutoMLDatasetDefinition\": {\
                \"AutoMLSnowflakeDatasetDefinition\": {\
                    \"Warehouse\": contextHeaders[\"sf-context-current-warehouse\"],\
                    \"Database\": databaseName,\
                    \"Schema\": schemaName,\
                    \"TableName\": targetTable,\
                    \"SnowflakeRole\": \"%s\",\
                    \"SecretArn\": \"%s\",\
                    \"OutputS3Uri\": s3OutputUri + jobDatasetsPath,\
                    \"StorageIntegration\": \"%s\"\
                }\
                }\
            }\
            ],\
            \"OutputDataConfig\": {\
            \"S3OutputPath\": s3OutputUri\
            },\
            \"RoleArn\": \"%s\"\
        };\
        \
        if (objectiveMetric) { \
            payload[\"AutoMLJobObjective\"] = { \
                \"MetricName\": objectiveMetric\
            };\
        }\
        if (problemType) { \
            payload[\"ProblemType\"] = problemType;\
        }\
        if (kmsKeyArn) { \
            payload[\"OutputDataConfig\"][\"KmsKeyId\"] = kmsKeyArn;\
            payload[\"InputDataConfig\"][\"AutoMLSnowflakeDatasetDefinition\"][\"KmsKeyId\"] = kmsKeyArn;\
            payload[\"AutoMLJobConfig\"][\"SecurityConfig\"] = { \
                \"VolumeKmsKeyId\": kmsKeyArn,\
                \"EnableInterContainerTrafficEncryption\": true\
            };\
        }\
        \
        return {\"body\": JSON.stringify(payload)}; \
        $$;") % (s3_bucket_name, kms_key_arn, snowflake_role_name, secret_arn, storage_integration_name, auto_ml_role_arn)

    snowflake_cursor.execute(createmodel_serializer_str)

    createmodel_deserializer_str = ("create or replace function AWS_AUTOPILOT_CREATE_MODEL_DESERIALIZER(EVENT OBJECT) \
        returns OBJECT LANGUAGE JAVASCRIPT AS \
        $$ \
        let arn = EVENT.body.AutoMLJobArn; \
        let message = \"Model creation in progress. Job ARN = \" + arn; \
        return {\"body\": {   \"data\" : [[0, message]]  }} \
        $$;")

    snowflake_cursor.execute(createmodel_deserializer_str)

    create_createmodel_ef_str = ("create or replace external function AWS_AUTOPILOT_CREATE_MODEL(modelname varchar, targettable varchar, targetcol varchar) \
    returns variant \
    api_integration = \"%s\" \
    context_headers  = (CURRENT_DATABASE, CURRENT_SCHEMA, CURRENT_WAREHOUSE) \
    serializer = AWS_AUTOPILOT_CREATE_MODEL_SERIALIZER \
    deserializer=AWS_AUTOPILOT_CREATE_MODEL_DESERIALIZER \
    max_batch_rows=1 \
    as '%s/createmodel';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_createmodel_ef_str)

    create_createmodel_ef_str2 = ("create or replace external function AWS_AUTOPILOT_CREATE_MODEL(modelname varchar, targettable varchar, \
    targetcol varchar, objective_metric varchar, problem_type varchar, max_running_time integer, deploy_model boolean, model_endpoint_ttl integer) \
    returns variant \
    api_integration = \"%s\" \
    context_headers  = (CURRENT_DATABASE, CURRENT_SCHEMA, CURRENT_WAREHOUSE) \
    serializer = AWS_AUTOPILOT_CREATE_MODEL_SERIALIZER \
    deserializer=AWS_AUTOPILOT_CREATE_MODEL_DESERIALIZER \
    max_batch_rows=1 \
    as '%s/createmodel';") % (api_integration_name, api_gateway_url)

    snowflake_cursor.execute(create_createmodel_ef_str2)


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
