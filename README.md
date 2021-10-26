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
* snowflakeRole (Optional): "Snowflake Role with permissions to create Storage and API Integrations"
* snowflakeDatabaseName: "Snowflake Database in which external functions will be created"
* snowflakeSchemaName: "Snowflake Database Schema in which external functions will be created"
* apiGatewayName (Optional): "API Gateway name"
* apiGatewayStageName (Optional): "API Gateway stage name"
* snowflakeResourceSuffix (Optional): "Suffix for resources created in Snowflake. This suffix will be added to all function names created in the database schema."

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
ParameterKey=snowflakeRole,ParameterValue=SNOWFLAKE_ROLE \
ParameterKey=snowflakeDatabaseName,ParameterValue=SNOWFLAKE_DATABASE_NAME \
ParameterKey=snowflakeSchemaName,ParameterValue=SNOWFLAKE_SCHEMA_NAME \
ParameterKey=apiGatewayName,ParameterValue=API_GW_NAME \
ParameterKey=apiGatewayStageName,ParameterValue=API_GW_STAGE_NAME \
ParameterKey=snowflakeResourceSuffix,ParameterValue=SUFFIX
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
% zip -r snowflake-connector-python-<version>.zip .
```

These commands will generate a file called *snowflake-connector-python-<version>.zip* containing the libraries for the Lambda.

You can then upload the generated file in your S3 bucket and use the corresponding S3 URL as a reference for your Lambda layer.

### Generate ZIP file containing the Lambda code

In order to load the libraries, the Lambda function can't be specified inline on the CloudFormation template (it will be visible and editable for the customers once the stack was created).

As such, we need to ZIP the Lambda Python code and upload it in the same S3 bucket where we already uploaded the layer ZIP file in the previous step.

From a Linux terminal, run:

```
% cd customer-stack/
zip -r create-resources-<version>.zip create-resources.py
```

These commands will generate a file called *create-resources-<version>.zip* containing the Lambda code.

You can then upload the generated file in your S3 bucket and use the corresponding S3 URL as a reference for your Lambda function code.

# APIs

For detailed documentation on the APIs provided by the stack, please refer to the Snowflake public documentation.
