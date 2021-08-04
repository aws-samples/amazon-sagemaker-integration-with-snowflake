# Amazon SageMaker Integration with Snowflake

You can use the CloudFormation template provided in this repository to add machine-learning capabilities to your Snowflake account using Amazon SageMaker.

In order to use this package, you need a Snowflake account and an AWS account.
After a few manual steps, the CloudFormation template can be deployed to your AWS account in order to create all the AWS resources (API Gateway, Lambda) and Snowflake resources (external functions) required.

The instructions that follow allow you to set up and deploy the CloudFormation template for development/debugging/testing purposes. For a quick start user guide on how to set up your Snowflake account with Amazon SageMaker, please refer to the Snowflake public documentation.

# Preparation

These are the steps to prepare the CloudFormation template (customer-stack.yml) to be executable.

## Snowflake Resources needed

Load a tabular dataset (i.e. a CSV file) into Snowflake and put it on a Snowflake table. For instance, you can use the Abalone data, originally from the UCI data repository (https://archive.ics.uci.edu/ml/datasets/abalone).

## Create an AWS secret containing the Credentials to access your Snowflake account

The credentials to access Snowflake must be stored on a Secret in AWS Secret Manager. In order to set that up:

1. Go to the Secrets Manager console.
2. Click on *Store a new Secret*
3. Select *Other type of secrets*
4. On the *Secret key/value* tab fill 3 key/value rows:

   * accountid (this contains your Snowflake account id)
   * username (this contains your Snowflake username)
   * password (this contains your Snowflake password)

If you click *Plaintext* you should see something like this:

```
{
  "accountid": "your_account_id",
  "username": "your_username",
  "password": "your_password"
}
```

5. Leave the default encryption key selected and click next.
6. Give a name to your Secret and click next (for example: mySecret).

# Creation of the stack

## CloudFormation Parameters

These parameters are needed to create the stack.

* s3BucketName: "Name of the S3 bucket to be created to store the training data and artifacts produced by the SageMaker AutoML jobs"
* snowflakeSecretArn: "ARN of the AWS Secret containing the Snowflake login information"
* kmsKeyArn (Optional): "ARN of the AWS Key Management Service key that Amazon SageMaker uses to encrypt job outputs. The KmsKeyId is applied to all outputs."
* vpcSecurityGroupIds (Optional): "Comma delimited list of security group ids for VPC configuration"
* vpcSubnetIds (Optional): "Comma delimited list of subnet ids for VPC configuration"
* snowflakeRole (Optional): "Snowflake Role with permissions to create Storage and API Integrations"
* snowflakeDatabaseName: "Snowflake Database in which external functions will be created"
* snowflakeSchemaName: "Snowflake Database Schema in which external functions will be created"
* apiGatewayName (Optional): "API Gateway name"
* apiGatewayStageName (Optional): "API Gateway stage name"
* codeBucket (Optional): "Name of the S3 bucket containing the code. Default is `sagemaker-sample-files` (public S3 bucket)"
* pathToLayerCode (Optional): "Path within codeBucket where the layer code is. Default is a location to public S3 bucket `sagemaker-sample-files`."
* pathToLambdaCode (Optional): "Path within codeBucket where the lambda code is. Default is a location to public S3 bucket `sagemaker-sample-files`."

## Create the stack via the CLI

You can create the stack via CLI by using these command:

```
aws cloudformation create-stack \
--region YOUR_REGION \
--stack-name myteststack \
--template-body file://path/to/customer-stack.yml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters ParameterKey=s3BucketName,ParameterValue=S3_BUCKET_NAME \
ParameterKey=snowflakeSecretArn,ParameterValue=CREDENTIALS_SECRET_ARN \
ParameterKey=kmsKeyArn,ParameterValue=KMS_KEY_ARN \
ParameterKey=vpcSecurityGroupIds,ParameterValue=SG_GROUP1\\,SG_GROUP2 \
ParameterKey=vpcSubnetIds,ParameterValue=SUBNET_1\\,SUBNET_2 \
ParameterKey=snowflakeRole,ParameterValue=SNOWFLAKE_ROLE \
ParameterKey=snowflakeDatabaseName,ParameterValue=SNOWFLAKE_DATABASE_NAME \
ParameterKey=snowflakeSchemaName,ParameterValue=SNOWFLAKE_SCHEMA_NAME \
ParameterKey=apiGatewayName,ParameterValue=API_GW_NAME \
ParameterKey=apiGatewayStageName,ParameterValue=API_GW_STAGE_NAME \
ParameterKey=codeBucket,ParameterValue=NAME_OF_THE_CODE_BUCKET \
ParameterKey=pathToLayerCode,ParameterValue=KEY_OF_LAYER_CODE \
ParameterKey=pathToLambdaCode,ParameterValue=KEY_OF_LAMBDA_CODE
```

**Note:** If the stack was created already, you can update it by changing *create-stack* by *update-stack* on the previous command.

## Create the stack via the Console

If you want to do it via the console:

* Go to CloudFormation
* Create stack with new resources
* Upload template file
* Set the parameters
* Click Next
* Write the template name
* Click next to create the resources


# API documentation
## CREATE_MODEL
### Synopsis

The CREATE_MODEL calls accept the input on the body:

```
{
  "ModelName": "String: model name",
  "TableName": "String: Table name",
  "TargetColumn": "String: Target attribute name",
  "ObjectiveMetric": "String: Metric Name",
  "ProblemType": "Enum: Auto|BinaryClassification|MulticlassClassification|Regression",
  "MaxTime": Long: Maxtime in seconds for the AutoML Job,
  "ModelDeployConfig": {
    "ModelDeployMode": "Enum: Model deployment mode: Model|EndpointConfig|Endpoint",
    "EndpointConfigDefinitions": [
      {
        "EndpointConfigName": "String: Name of the endpoint configuration",
        "InitialInstanceCount": Integer: Initial number of instances,
        "InstanceType": "String: AWS Instance type"
      },
      [...]
    ],
    "EndpointDefinitions": [
      {
        "EndpointName": "String: Endpoint name",
        "EndpointConfigName": "String: Name of the endpoint configuration to use",
        "DeletionCondition": {
          "MaxRuntimeInSeconds": Long: Max time in seconds for the endpoint to run
        }
      },
      [...]
    ]
  },
  "Warehouse": "String: Snowflake Warehouse name",
  "Database": "String: Snowflake Database name",
  "Schema": "String: Snowflake Schema name"
}
```

This Method returns an empty JSON:

```
{}
```

### Example
#### Console

* Access the API Gateway Console on the region you created your stack.

* Enter the *SageMakerSnowflakeApiGateway* API

* Click on the *POST* right behind */createmodel*

* Click on *TEST*

* On the Request Body, add a JSON specifying the fields:

```
{
  "ModelName": "testModel",
  "TableName": "ABALONE",
  "TargetColumn": "RINGS",
  "ObjectiveMetric": "Accuracy",
  "ProblemType": "MulticlassClassification",
  "ModelDeployConfig": {
    "ModelDeployMode": "Endpoint",
    "EndpointConfigDefinitions": [
      {
        "EndpointConfigName": "testModel-m5-2xl-1",
        "InitialInstanceCount": 1,
        "InstanceType": "ml.m5.2xlarge"
      },
      {
        "EndpointConfigName": "testModel-m5-4xl-2",
        "InitialInstanceCount": 2,
        "InstanceType": "ml.m5.4xlarge"
      },
      {
        "EndpointConfigName": "testModel-m5-24xl-3",
        "InitialInstanceCount": 3,
        "InstanceType": "ml.m5.24xlarge"
      }
    ],
    "EndpointDefinitions": [
      {
        "EndpointName": "testModel",
        "EndpointConfigName": "testModel-m5-24xl-3",
        "DeletionCondition": {
          "MaxRuntimeInSeconds": 7200
        }
      }
    ]
  },
  "Warehouse": "WAREHOUSE_NAME",
  "Database": "DATABASE_NAME",
  "Schema": "PUBLIC"
}
```

If it works, the logs will show an ARN for *testModel*, something like:

```
arn:aws:sagemaker:YOUR_REGION:YOUR_ACCOUNT_ID:automl-job/testModel-job
```

After the corresponding AutoMLJob has completed (may take minutes), you can check that the best model found was deployed to a SageMaker Endpoint via the AWS Console:

* Open the SageMaker Console on the region where your CloudFormation template was created.

* On the left bar expand *Inference* and click on *Endpoints*.

* You will see an endpoint with name *testModel* in the list.

#### CLI

In order to use the CLI, you'll need the identifiers for your *SageMakerSnowflakeApiGateway* API and */createmodel* Resource from API Gateway. This information can be found on the CLI:

```
aws apigateway get-rest-apis
aws apigateway get-resources --rest-api-id CHANGEME_API_ID
```

Once you have the API and resource identifier, you can execute the next command

```
 aws apigateway test-invoke-method \
 --rest-api-id CHANGEME_API_ID \
 --resource-id CHANGEME_CREATEMODEL_RESOURCE_ID \
 --http-method POST \
 --body '{ "ModelName": "testModel", "TableName": "ABALONE", "TargetColumn": "RINGS", "ObjectiveMetric": "Accuracy", "ProblemType": "MulticlassClassification", "MaxTime": Long: Maxtime in seconds for the AutoML Job, "ModelDeployConfig": { "ModelDeployMode": "Endpoint", "EndpointConfigDefinitions": [ { "EndpointConfigName": "testModel-m5-2xl-1", "InitialInstanceCount": 1, "InstanceType": "ml.m5.2xlarge" }, { "EndpointConfigName": "testModel-m5-4xl-2", "InitialInstanceCount": 2, "InstanceType": "ml.m5.4xlarge" }, { "EndpointConfigName": "testModel-m5-24xl-3", "InitialInstanceCount": 3, "InstanceType": "ml.m5.24xlarge" } ], "EndpointDefinitions": [ { "EndpointName": "testModel", "EndpointConfigName": "testModel-m5-24xl-3", "DeletionCondition": { "MaxRuntimeInSeconds": 7200 } } ] }, "Warehouse": "WAREHOUSE_NAME", "Database": "DATABASE_NAME", "Schema": "PUBLIC" }'
```

You can check that your model has been deployed using *list-endpoints*:

```
aws sagemaker list-endpoints
```

*Example:*

```
% aws sagemaker list-endpoints
{
  "Endpoints": [
    {
      "EndpointName": "testModel",
      "EndpointArn": "arn:aws:sagemaker:YOUR_REGION:YOUR_ACCOUNT_ID:endpoint/testModel",
      "CreationTime": XXYYZZ,
      "LastModifiedTime": XXYYZZ,
      "EndpointStatus": "InService"
    }
  ]
}
```

## PREDICT_OUTCOME
### Synopsis

The PREDICT_OUTCOME calls receives input both in the body and in the path:

Path:

The model name is passed in the path using the *endpointName* variable (this will be the value after predictoutcome)

*Example:*

```
https://api_gateway_url/sagemaker/stagename/predictoutcome/testEndpoint
```

Body:

The data for the predictions is passed in the body.

```
value0,value1,...,valueN
value0,value1,...,valueN
...
value0,value1,...,valueN
```

The Output will be a JSON in the format returned by the SageMaker endpoint (https://docs.aws.amazon.com/sagemaker/latest/dg/LL-in-formats.html):

```
{
  "predictions": [
    {
      "predicted_label": "predictedLabel1",
      "probability": "probability1"
    },
    {
      "predicted_label": "predictedLabel2",
      "probability": "probability2"
    },
...
    {
      "predicted_label": "predictedLabelM",
      "probability": "probabilityM"
    }
  ]
}
```

### Example
#### Console

* Access the API Gateway Console on the region you created your stack.

* Enter the *SageMakerSnowflakeApiGateway* API

* Click on the *POST* right behind */{endpointName}*.

* Click on *TEST*

* On the Path parameter for *{endpointName}*, add the name of your endpoint *testEndpoint*.

* On the Request Body, add the CSV with the data to invoke the endpoint:

```
M,0.455,0.365,0.095,0.514,0.2245,0.101,0.15
M,0.35,0.265,0.09,0.2255,0.0995,0.0485,0.07
F,0.53,0.42,0.135,0.677,0.2565,0.1415,0.21
M,0.44,0.365,0.125,0.516,0.2155,0.114,0.155
I,0.33,0.255,0.08,0.205,0.0895,0.0395,0.055
I,0.425,0.3,0.095,0.3515,0.141,0.0775,0.12
F,0.53,0.415,0.15,0.7775,0.237,0.1415,0.33
F,0.545,0.425,0.125,0.768,0.294,0.1495,0.26
M,0.475,0.37,0.125,0.5095,0.2165,0.1125,0.165
```

If it works, the output will show the predicted values in the format specified in Snowflake's doc (https://docs.snowflake.com/en/sql-reference/external-functions-data-format.html#data-format-received-by-snowflake):

```
{
  "predictions": [
    {
      "predicted_label": "8",
      "probability": "0.2730035185813904"
    },
    {
      "predicted_label": "7",
      "probability": "0.28385308384895325"
    },
    {
      "predicted_label": "10",
      "probability": "0.21687646210193634"
    },
    {
      "predicted_label": "10",
      "probability": "0.19842849671840668"
    },
    {
      "predicted_label": "6",
      "probability": "0.39686068892478943"
    },
    {
      "predicted_label": "7",
      "probability": "0.3740205764770508"
    },
    {
      "predicted_label": "13",
      "probability": "0.1785871386528015"
    },
    {
      "predicted_label": "10",
      "probability": "0.18686321377754211"
    },
    {
      "predicted_label": "9",
      "probability": "0.23011770844459534"
    }
  ]
}
```

#### CLI

In order to use the CLI, you'll need the identifiers for your *SageMakerSnowflakeApiGateway* API and */sagemaker/predictoutcome* Resource from API Gateway. This information can be found on the CLI:

```
aws apigateway get-rest-apis
aws apigateway get-resources --rest-api-id CHANGEME_API_ID
```

Once you have the API and resource identifier, you can execute the next command

```
aws apigateway test-invoke-method \
--rest-api-id CHANGEME_API_ID \
--resource-id CHANGEME_PREDICTOUTCOME_RESOURCE_ID \
--http-method POST \
--body 'M,0.455,0.365,0.095,0.514,0.2245,0.101,0.15\nM,0.35,0.265,0.09,0.2255,0.0995,0.0485,0.07\nF,0.53,0.42,0.135,0.677,0.2565,0.1415,0.21\nM,0.44,0.365,0.125,0.516,0.2155,0.114,0.155\nI,0.33,0.255,0.08,0.205,0.0895,0.0395,0.055\nI,0.425,0.3,0.095,0.3515,0.141,0.0775,0.12\nF,0.53,0.415,0.15,0.7775,0.237,0.1415,0.33\nF,0.545,0.425,0.125,0.768,0.294,0.1495,0.26\nM,0.475,0.37,0.125,0.5095,0.2165,0.1125,0.165' \
--path-with-query-string '/sagemaker/predictoutcome/testEndpoint'
```

## DELETE_ENDPOINT
### Synopsis

DELETE_ENDPOINT will receive the name of an endpoint and delete it.

Body:

```
{
  "EndpointName": "String: Entpoint name to delete"
}
```

*Output:*

```
{}
```

### Example
#### Console

* Access the API Gateway Console on the region you created your stack.

* Enter the *SageMakerSnowflakeApiGateway* API

* Click on the *POST* right behind */deleteendpoint*

* Click on *TEST*

* On the Request Body, add a JSON with the data to :

```
{
  "EndpointName": "testEndpoint"
}
```

You can check the endpoint was deleted in the same way explained above to verify the endpoint creation.

#### CLI

In order to use the CLI, you'll need the identifiers for your *SageMakerSnowflakeApiGateway* API and */sagemaker/deleteendpoint* Resource from API Gateway. This information can be found on the CLI:

```
aws apigateway get-rest-apis
aws apigateway get-resources --rest-api-id CHANGEME_API_ID
```

Once you have the API and resource identifier, you can execute the next command

```
aws apigateway test-invoke-method \
--rest-api-id CHANGEME_API_ID \
--resource-id CHANGEME_deleteendpoint_RESOURCE_ID \
--http-method POST \
--body '{"EndpointName": "testEndpoint"}'
```

You can check the endpoint was deleted in the same way explained above to verify the endpoint creation.

## CREATE_ENDPOINT
### Synopsis

CREATE_ENDPOINT will receive the endpoint configuration and the endpoint name to create an endpoint.

Body:

```
{
  "EndpointConfigName": "String: Name of the configuration to use",
  "EndpointName": "String: Name of the endpoint",
  "DeletionCondition": {
    "MaxRuntimeInSeconds": Long: Max time in seconds for the endpoint to run
  }
}
```

*Output:*

```
{}
```

### Example
#### Console

Access the API Gateway Console on the region you created your stack.

Enter the *SageMakerSnowflakeApiGateway* API

Click on the *POST* right behind */createendpoint*

Click on *TEST*

On the Request Body, add a JSON with the data to :

```
{
  "EndpointConfigName": "testModel-m5-2xl-1",
  "EndpointName": "testEndpoint1",
  "DeletionCondition": {
    "MaxRuntimeInSeconds": 7200
  }
}
```

You can check the endpoint was created in the same way explained above to verify the endpoint creation.

#### CLI

In order to use the CLI, you'll need the identifiers for your *SageMakerSnowflakeApiGateway* API and */sagemaker/createendpoint* Resource from API Gateway. This information can be found on the CLI:

```
aws apigateway get-rest-apis
aws apigateway get-resources --rest-api-id CHANGEME_API_ID
```

Once you have the API and resource identifier, you can execute the next command

```
aws apigateway test-invoke-method \
--rest-api-id CHANGEME_API_ID \
--resource-id CHANGEME_createendpoint_RESOURCE_ID \
--http-method POST \
--body '{"EndpointConfigName": "testModel-m5-2xl-1","EndpointName": "testEndpoint1","DeletionCondition": {"MaxRuntimeInSeconds": 7200}}'
```

You can check the endpoint was created in the same way explained above to verify the endpoint creation.

## DESCRIBE_MODEL
### Synopsis

DESCRIBE_MODEL will return the information for the model name sent.

Body:


```
{
  "ModelName": "String: Model name to describe"
}
```

*Output:*

```
{
  "ObjectiveMetric": "String: Objective metric name",
  "BestObjectiveMetric": Number: Objective metric value,
  "JobStatus": "String: Status of the AutoML Job",
  "JobStatusDetails": "String: Secondary status of the AutoML job",
  "FailureReason": "String: Failure reason of the AutoML job"
}
```

### Example
#### Console

* Access the API Gateway Console on the region you created your stack.

* Enter the *SageMakerSnowflakeApiGateway* API

* Click on the *POST* right behind */describemodel*

* Click on *TEST*

* On the Request Body, add a JSON with the data to :

```
{
  "ModelName": "testModel"
}
```

On the output you'll see something like this:

```
{
  "ObjectiveMetric": "validation:accuracy",
  "BestObjectiveMetric": 0.2736000120639801,
  "JobStatus": "Completed",
  "JobStatusDetails": "Completed",
  "FailureReason": ""
}
```

#### CLI

In order to use the CLI, you'll need the identifiers for your *SageMakerSnowflakeApiGateway* API and */sagemaker/describemodel* Resource from API Gateway. This information can be found on the CLI:

```
aws apigateway get-rest-apis
aws apigateway get-resources --rest-api-id CHANGEME_API_ID
```

Once you have the API and resource identifier, you can execute the next command

```
aws apigateway test-invoke-method \
--rest-api-id CHANGEME_API_ID \
--resource-id CHANGEME_DESCRIBEMODEL_RESOURCE_ID \
--http-method POST \
--body '{"ModelName": "testModel"}'
```

On the output you'll see something like this:

```
{
  "ObjectiveMetric": "validation:accuracy",
  "BestObjectiveMetric": 0.2736000120639801,
  "JobStatus": "Completed",
  "JobStatusDetails": "Completed",
  "FailureReason": ""
}
```
## DESCRIBE_ENDPOINT
### Synopsis

DESCRIBE_ENDPOINT will receive the name of an endpoint.

Body:

```
{
  "EndpointName": "String: Endpoint name to describe"
}
```

*Output:*

```
{
  "EndpointStatus": "String: Status of the endpoint"
  "FailureReason": "String: Reason for the endpoint creation to fail"
}
```

### Example
#### Console

* Access the API Gateway Console on the region you created your stack.

* Enter the *SageMakerSnowflakeApiGateway* API

* Click on the *POST* right behind */describeendpoint*

* Click on *TEST*

* On the Request Body, add a JSON with the data to :

```
{
  "EndpointName": "testEndpoint"
}
```

Click test and you'll see something like this on the output:

```
{
  "EndpointStatus": "InService"
  "FailureReason": ""
}
```

#### CLI

In order to use the CLI, you'll need the identifiers for your *SageMakerSnowflakeApiGateway* API and */sagemaker/describeendpoint* Resource from API Gateway. This information can be found on the CLI:

```
aws apigateway get-rest-apis
aws apigateway get-resources --rest-api-id CHANGEME_API_ID
```

Once you have the API and resource identifier, you can execute the next command

```
aws apigateway test-invoke-method \
--rest-api-id CHANGEME_API_ID \
--resource-id CHANGEME_deleteendpoint_RESOURCE_ID \
--http-method POST \
--body '{"EndpointName": "testEndpoint"}'
```

You can check the endpoint was deleted the same way it is explained on *HOWTO deploy the model*.

## Generate and upload Layer and Lambda code to an existing S3 bucket

The Snowflake Python connector is not part of the AWS Lambda runtime. In order to load the Snowflake Python connectior into Lambda, we need to use a Lambda layer.

Lambda layers take a ZIP file with the libraries (formatted according to the language used https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html) from S3 and loads them into the Lambda runtime environment.

The Lambda layer ZIP file is hosted in a publicly accessible S3 bucket (`sagemaker-sample-files`) that this CloudFormation template refers to. In case you wish to generate the layer manually (for development/testing), please follow the instructions below.

### Generate ZIP file containing the Layer code

The script *generate-layer.sh* located in the *customer-stack/* directory will be the responsible of downloading the needed files.

In order to execute it, from a Linux terminal run:

```
% cd customer-stack/
% bash generate-layer.sh
% cd layer/snowflake-connector-python/
% zip -r snowflake-connector-python-1.0.zip .
```

These commands will generate a file called *snowflake-connector-python-1.0.zip* containing the libraries for the Lambda.

You can then upload the generated file in your S3 bucket and use the corresponding S3 URL as a reference for your Lambda layer.

### Generate ZIP file containing the Lambda code

In order to load the libraries, the Lambda function can't be specified inline on the CloudFormation template (it will be visible and editable for the customers once the stack was created).

As such, we need to ZIP the Lambda Python code and upload it in the same S3 bucket where we already uploaded the layer ZIP file in the previous step.

From a Linux terminal, run:

```
% cd customer-stack/
zip -r create-resources-1.0.zip create-resources.py
```

These commands will generate a file called *create-resources-1.0.zip* containing the Lambda code.

You can then upload the generated file in your S3 bucket and use the corresponding S3 URL as a reference for your Lambda function code.