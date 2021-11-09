## 

[[Snowflake + Amazon SageMaker Autopilot Integration
Overview]{.ul}](#snowflake-amazon-sagemaker-autopilot-integration-overview)

[[Solution Architecture]{.ul}](#solution-architecture)

> [[Solution Overview]{.ul}](#solution-overview)
>
> [[Setup]{.ul}](#setup)

[[Getting Started]{.ul}](#getting-started)

> [[Planning the deployment]{.ul}](#planning-the-deployment)
>
> [[Deploying the CloudFormation
> template]{.ul}](#deploying-the-cloudformation-template)

[[Working with SageMaker API's from
Snowflake]{.ul}](#working-with-sagemaker-apis-from-snowflake)

> [[Create Model]{.ul}](#create-model)
>
> [[Describe Model]{.ul}](#describe-model)
>
> [[Predict Outcome]{.ul}](#predict-outcome)
>
> [[Create Endpoint Config]{.ul}](#create-endpoint-config)
>
> [[Describe Endpoint Config]{.ul}](#describe-endpoint-config)
>
> [[Delete Endpoint Config]{.ul}](#delete-endpoint-config)
>
> [[Create Endpoint]{.ul}](#create-endpoint)
>
> [[Describe Endpoint]{.ul}](#describe-endpoint)
>
> [[Delete Endpoint]{.ul}](#delete-endpoint)

[[Costs]{.ul}](#costs)

## Snowflake + Amazon SageMaker Autopilot Integration Overview

Organizations are increasingly using Snowflake to unify, integrate,
analyze, and share previously fragmented data, and want to use state of
the art machine learning (ML) to glean business insights. However,
development of ML models based on large datasets requires extensive
programming expertise and knowledge of ML frameworks. Meanwhile, most
organizations have teams of analysts with the domain knowledge necessary
to build ML models but lack the machine learning expertise required to
train and deploy them. To address this, Snowflake is now integrated with
Amazon SageMaker Autopilot to enable analysts and other SQL users to
automatically build and deploy state-of-the-art machine learning models.

Snowflake + Amazon SageMaker Autopilot Integration enables users to:

-   **Create and manage ML models**: Use standard SQL queries in
    > Snowflake to access Autopilot APIs and automatically create the
    > best machine learning model for your data in Snowflake. Autopilot
    > does all the heavy lifting by automatically exploring, training,
    > and tuning different ML algorithms, and providing the model that
    > best fits your data.

-   **Make predictions**: Use standard SQL queries to deploy, invoke and
    > manage ML models to SageMaker endpoints and make predictions from
    > within Snowflake.

## Solution Architecture

### **Solution Overview**

Snowflake + Amazon SageMaker Autopilot Integration sets up a reference
architecture that allows you to directly access Amazon SageMaker machine
learning (ML) APIs in Snowflake. The application it deploys is powered
by Snowflake's [[external
functions]{.ul}](https://docs.snowflake.com/en/sql-reference/external-functions-introduction.html)
and [[custom
serializers]{.ul}](https://docs.snowflake.com/en/LIMITEDACCESS/external-functions-serializers.html)
features, which allow you to directly create, use, and make predictions
from SageMaker machine learning models using simple SQL commands.

![](media/image1.png){width="6.5in" height="2.361111111111111in"}Fig 1.
Snowflake + Amazon SageMaker Autopilot Solution Architecture

1.  When a supported AWS_AUTOPILOT SQL command is executed, the UI
    > client program passes Snowflake a SQL statement that calls an
    > external function.

> As part of query execution, Snowflake reads the external function
> definition, which contains the URL of the API Gateway service and the
> name of the API integration that contains authentication information
> for that proxy service. It also passes the data for formatting through
> any serializers/deserializers associated with the external function.

2.  Snowflake then reads information from the API integration and
    > composes an HTTP POST request that contains the headers, data to
    > be sent and authentication information and forwards the requests
    > to the API Gateway.

3.  API Gateway then forwards the call to the respective SageMaker API.

### **Setup**

The integration provides a reference AWS
[[CloudFormation]{.ul}](https://aws.amazon.com/cloudformation/resources/templates/)
template that sets up the required resources on AWS and Snowflake. The
template aims to automate as much of the setup and act as a starting
point and can be extended as needed. Deploying the CloudFormation
template using the default parameters builds the following serverless
environment:

![](media/image2.png){width="6.5in" height="2.9027777777777777in"}

Fig 2. AWS Cloudformation Template Setup

The CloudFormation template transparently and automatically creates the
following

**AWS Resources:**

-   **Amazon API Gateway** REST API with endpoints to facilitate
    > connection between Snowflake external functions and SageMaker
    > API's. See [[Amazon API Gateway
    > documentation]{.ul}](https://docs.aws.amazon.com/apigateway/index.html)
    > to learn more about the service.

-   **S3 bucket** to store the training data and model artifacts created
    > by Autopilot. See [[S3
    > documentation]{.ul}](https://aws.amazon.com/s3/getting-started/)
    > to learn more about the service.

-   **AWS Lambda** which acts as a setup Lambda function that uses the
    > Snowflake Python connector and credentials stored in the AWS
    > Secrets manager to connect to and setup resources in Snowflake.
    > See [[AWS Lambda
    > documentation]{.ul}](https://docs.aws.amazon.com/lambda/index.html)
    > to learn more about the service.

-   **IAM roles** to access the resources and set up trust relationships
    > between Snowflake and the Amazon API Gateway. See [[IAM roles
    > documentation]{.ul}](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
    > to learn more about the service. See Snowflake documentation to
    > learn more on [[linking the API integration object in Snowflake to
    > Amazon API Gateway using IAM
    > roles]{.ul}](https://docs.snowflake.com/en/sql-reference/external-functions-creating-aws-common-api-integration-proxy-link.html).

**Snowflake Resources:**

-   **Storage Integration** required to copy data from a Snowflake table
    > to an Amazon S3 bucket for training. See Snowflake's documentation
    > on [[Storage
    > Integrations]{.ul}](https://docs.snowflake.com/en/sql-reference/sql/create-storage-integration.html)
    > to learn more.

-   **API Integration** required by the Snowflake external functions to
    > talk to Amazon API Gateway. See Snowflake's documentation on [[API
    > Integrations]{.ul}](https://docs.snowflake.com/en/sql-reference/sql/create-api-integration.html)
    > to learn more.

-   **External functions and associated custom
    > serializers/deserializers** that correspond to various SageMaker
    > calls. See Snowflake's documentation on [[External
    > Functions]{.ul}](https://docs.snowflake.com/en/sql-reference/external-functions-introduction.html)
    > and [[Custom
    > Serializers]{.ul}](https://docs.snowflake.com/en/LIMITEDACCESS/external-functions-serializers.html)
    > to learn more.

## Getting Started

### Planning the deployment

Before you deploy the CloudFormation template, review the following
information and ensure that your AWS and Snowflake accounts are properly
configured and you have the right set of permissions. Otherwise,
deployment might fail.

**Snowflake account** - If you don't already have a Snowflake account,
create one at
[[https://signup.snowflake.com/]{.ul}](https://signup.snowflake.com/).
As SageMaker runs on the AWS cloud, for best performance it is
recommended to use a Snowflake AWS deployment.

**AWS account -** If you don't already have an AWS account, create one
at [[https://aws.amazon.com]{.ul}](https://aws.amazon.com). Your AWS
account is automatically signed up for all AWS services. You are charged
only for the services you use.

**AWS services quotas\
**The resources created by the CloudFormation template provided should
not exceed any service quota for your AWS account.\
Should any service quota exceed the limit, you can verify your limits
and ask for quota increases in the [[Service Quotas
console]{.ul}](https://console.aws.amazon.com/servicequotas/home?region=us-east-2#!/).\
\
When creating models and performing predictions, Snowflake will create
AutoML jobs and SageMaker Endpoints in your AWS account.\
This can result in reaching the [[SageMaker service
quotas]{.ul}](https://docs.aws.amazon.com/general/latest/gr/sagemaker.html#limits_sagemaker)
for your AWS account. If you encounter error messages that you\'ve
exceeded your quota, use [[AWS
Support]{.ul}](https://console.aws.amazon.com/support/) to request a
service limit increase for the SageMaker resources you want to scale up.

**Permissions**

**AWS IAM permissions:** Before deploying the CloudFormation template,
you must sign in to the AWS Management Console with IAM permissions for
the resources that the templates deploy. The AdministratorAccess managed
policy within IAM provides sufficient permissions, although your
organization may choose to use a custom policy with more restrictions.
For more information, see [[AWS managed policies for job
functions]{.ul}](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_job-functions.html).

**Snowflake permissions:** In order for the template to create the
required Snowflake resources, you will need to have a Snowflake role
with permissions to create Storage Integrations, API Integrations and
Functions. This could be the Account Administrator role or a custom role
with the above privileges. See Snowflake
[[roles]{.ul}](https://docs.snowflake.com/en/user-guide/security-access-control-overview.html#roles)
and
[[privileges]{.ul}](https://docs.snowflake.com/en/user-guide/security-access-control-overview.html#privileges)
for more information.

**Storing Snowflake credentials in AWS Secrets Manager:** The
CloudFormation template takes as an input an ARN to an AWS Secret that
has the Snowflake account details and credentials to securely connect to
and create Snowflake resources required by the integration. To save your
credentials:

-   Go to the AWS Management Console.

-   From the top right corner select the AWS region, you plan to deploy
    > the template in. **Note:** It is required that you store your
    > secret in the same region you will be deploying the template in.

-   In the top search bar, search for **Secrets Manager**.

-   Click on **Store a new secret.**

-   Select **Other type of secrets.**

-   On the **Secret key/value** tab fill 3 key/value rows**:\
    > **username (this contains your Snowflake username)\
    > password (this contains your Snowflake password)\
    > accountid (this contains your Snowflake [[account
    > identifier]{.ul}](https://docs.snowflake.com/en/user-guide/admin-account-identifier.html))

-   If you click on the Plaintext tab you should see something like
    > this:\
    > {\
    > \"accountid\": \"snowflake_account_id\",\
    > \"username\": \"snowflake_user\",\
    > \"password\": \"snowflake_password\"\
    > }

-   Leave the default encryption key selected and click next.

-   Give a name to your Secret and click next.

-   You can leave the remaining options unchanged and click **Store** on
    > the final screen.

### Deploying the CloudFormation template

Sign in to your AWS account, and from the upper-right corner of the
navigation bar choose the Region you want the resources created by the
CloudFormation Template to be set up in. It is recommended to deploy the
AWS resources to the same region the Snowflake deployment runs on.

**Upload the template**

1.  Go to the AWS Management Console.

2.  In the top search bar, search for **CloudFormation**.

3.  Under Services, click on **CloudFormation**.

4.  Click on **Create stack**.\
    > If given a choice between **With new resources (standard)** or
    > **With existing resources (import resources)**, then choose **With
    > new resources (standard)**.

5.  On the **Create stack** page, under **Prepare template**, select
    > **Template is ready**.

6.  Select **Upload a template file**.

7.  Select **Choose file**.

8.  Navigate to the directory that contains your copy of the template,
    > then select that template.

9.  Click **Next** to reach the page on which you enter names for
    > resources, etc.

**Configure Your Options\
**The template contains default values for most fields. However, you
need to enter a few values, such as the names for the resources and the
ARN to the AWS Secret Manager.

1.  Enter a name for the stack.

2.  **apiGatewayName** - Enter the name of the API Gateway to be
    > created. Default name will be snowflake-autopilot-api.

3.  **apiGatewayStageName** - Enter the name of the API deployment stage
    > to be created. Default name will be snowflake-autopilot-stage.

4.  **s3BucketName** - Enter the name of the S3 bucket to be created to
    > store the training data and artifacts produced by the AutoML jobs.

5.  **kmsKeyArn** - Optional parameter. Enter ARN of the AWS Key
    > Management Service key that Amazon SageMaker can use to encrypt
    > job outputs. The KmsKeyId is applied to all outputs.

6.  **snowflakeDatabaseName** - Enter the name of the Snowflake Database
    > in which to create the external functions and custom serializers.

7.  **snowflakeSchemaName** - Enter the name of the Snowflake Database
    > Schema in which to create the external functions and custom
    > serializers.

8.  **snowflakeResourceSuffix -** Optional parameter. Enter a unique
    > suffix that can be appended to the Snowflake resources created.
    > This suffix will be added to all the functions created in the
    > provided Snowflake database schema.

> ***Note:** If you have multiple users deploying the template to the
> same Snowflake account and using the same Snowflake database and
> schemas it's recommended to provide the snowflakeResourceSuffix in
> order to prevent overriding of any existing resources deployed by
> other users.*

9.  **snowflakeRole** - Enter the name of the Snowflake Role with
    > permissions to create storage integrations, API integrations and
    > functions. Default value will be the ACCOUNTADMIN role.

10. **snowflakeSecretArn** - Enter the ARN of the secret from AWS
    > Secrets Manager containing the Snowflake login information.

11. Click **Next**.\
    > This page has some advanced options for template deployment.

    1.  Optionally, set advanced options, such as stack policy. These
        > are not needed when creating the sample function using the
        > template supplied by Snowflake.

    2.  Click **Next**.

12. On the review page, scroll down to the end and acknowledge that the
    > CloudFormation template might create IAM resources with custom
    > names. This is needed because the template creates three IAM roles
    > as part of the deployment.

13. Click on **Create stack**.

> The deployment will take a few seconds. After the deployment is
> complete, you should be on the **Events** tab for the newly created
> stack. The created resources will be listed under the **Resources**
> tab.
>
> If the deployment of the CloudFormation template was successful, you
> now have all the required resources created on the AWS and Snowflake
> side required for the integration.

## Working with SageMaker API's from Snowflake

1.  Login to your Snowflake account in which the resources have been
    > created by the CloudFormation template.

2.  The template should have set up:

    a.  Storage Integration with the name :
        > AWS_AUTOPILOT_STORAGE_INTEGRATION_YOURSTACKNAME

    b.  API Integration with the name:
        > AWS_AUTOPILOT_API_INTEGRATION_YOURSTACKNAME

> You can use the SHOW INTEGRATIONS LIKE \'%AWS_AUTOPILOT%\' SQL command
> to see the integrations created and use the [[DESCRIBE
> INTEGRATION]{.ul}](https://docs.snowflake.com/en/sql-reference/sql/desc-integration.html)
> command to get details on properties of a particular integration.
>
> **Note:** Since API and storage integrations are account-level
> objects, in order to avoid overriding existing integrations, the names
> are appended with the stack name provided as input during cloud
> formation template deployment.

c.  The following external functions and custom serializers(javascript
    > functions):

    i.  AWS_AUTOPILOT_CREATE_MODEL

    ii. AWS_AUTOPILOT_CREATE_MODEL_SERIALIZER

    iii. AWS_AUTOPILOT_CREATE_MODEL_DESERIALIZER

    iv. AWS_AUTOPILOT_DESCRIBE_MODEL

    v.  AWS_AUTOPILOT_DESCRIBE_MODEL_SERIALIZER

    vi. AWS_AUTOPILOT_DESCRIBE_MODEL_DESERIALIZER

    vii. AWS_AUTOPILOT_PREDICT_OUTCOME

    viii. AWS_AUTOPILOT_PREDICT_OUTCOME_SERIALIZER

    ix. AWS_AUTOPILOT_PREDICT_OUTCOME_DESERIALIZER

    x.  AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG

    xi. AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG_SERIALIZER

    xii. AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG_DESERIALIZER

    xiii. AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG

    xiv. AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG_SERIALIZER

    xv. AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG_DESERIALIZER

    xvi. AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG

    xvii. AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG_SERIALIZER

    xviii. AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG_DESERIALIZER

    xix. AWS_AUTOPILOT_CREATE_ENDPOINT

    xx. AWS_AUTOPILOT_CREATE_ENDPOINT_SERIALIZER

    xxi. AWS_AUTOPILOT_CREATE_ENDPOINT_DESERIALIZER

    xxii. AWS_AUTOPILOT_DESCRIBE_ENDPOINT

    xxiii. AWS_AUTOPILOT_DESCRIBE_ENDPOINT_SERIALIZER

    xxiv. AWS_AUTOPILOT_DESCRIBE_ENDPOINT_DESERIALIZER

    xxv. AWS_AUTOPILOT_DELETE_ENDPOINT

    xxvi. AWS_AUTOPILOT_DELETE_ENDPOINT_SERIALIZER

    xxvii. AWS_AUTOPILOT_DELETE_ENDPOINT_DESERIALIZER

> You can use SHOW FUNCTIONS LIKE \'%AWS_AUTOPILOT%\' SQL command to see
> all the functions created and use the [[DESCRIBE
> FUNCTION]{.ul}](https://docs.snowflake.com/en/sql-reference/sql/desc-function.html)
> command to get details on the specified function, including the
> signature (i.e. arguments), return value, language, and body (i.e.
> definition).
>
> **Note:** Since API and Storage integrations are account level
> objects, in order to avoid overriding existing integrations, the names
> are appended with the stack name provided as input during cloud
> formation template deployment.

### **Create Model**

> Use the below AWS_AUTOPILOT_CREATE_MODEL external functions to
> kick-off model creation on your data in a Snowflake table.
>
> **Option 1:**

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_CREATE_MODEL(MODELNAME VARCHAR, TRAINING_TABLE_NAME     |
| VARCHAR, TARGET_COL VARCHAR)                                          |
|                                                                       |
| **Arguments (all are required parameters):**\                         |
| MODELNAME - Name that will be used to refer to the best model found   |
| by Autopilot. Allowed Pattern:                                        |
| \^\[a-zA-Z0-9\](-\*\[a-zA-Z0-9\]){0,62}                               |
|                                                                       |
| TRAINING_TABLE_NAME - Name of the table from which to create the      |
| model. All rows will be considered to train the model.                |
|                                                                       |
| TARGET_COL - The name of the target column that we want the model to  |
| predict.                                                              |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_create_model (\'abalonemodel\',                  |
| \'abalone_training_dataset\', \'rings\')                              |
|                                                                       |
| **Expected output on success:**\                                      |
| \"Model creation in progress. Model ARN =                             |
| ar                                                                    |
| n:aws:sagemaker:us-west-2:631484165566:automl-job/abalonemodel-job.\" |
+=======================================================================+
+-----------------------------------------------------------------------+

-   The above command kicks off an AutoML job.

```{=html}
<!-- -->
```
-   The [**[Problem
    > type]{.ul}**](https://docs.aws.amazon.com/sagemaker/latest/dg/autopilot-problem-types.html)
    > and [**[Objective
    > metric]{.ul}**](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_AutoMLJobObjective.html#sagemaker-Type-AutoMLJobObjective-MetricName)
    > are auto inferred.

-   Depending on the size of the data the model, creation can take
    > anywhere from a few minutes for small data sets to 2-3 hours for
    > large datasets (eg. 5 GB). The default max run time of the AutoML
    > job is 86400 seconds. If you want more control on the model
    > creation time, you can use the advanced AWS_AUTOPILOT_CREATE_MODEL
    > option and set the MAX_RUNNING_TIME field. **Note:** The parameter
    > is intended to set a timeout on the length of the training job,
    > and if the job has not finished within the specified limit it is
    > forcefully stopped and a model will NOT be created. If you would
    > like to optimize for speed and have a model successfully created
    > in a shorter duration consider using the MAX_CANDIDATES parameter.

-   Use the [[AWS_AUTOPILOT_DESCRIBEMODEL]{.ul}](#describe-model)
    > function to check the status of the job.

-   Once the best model is found Autopilot transparently deploys the
    > model to a SageMaker Endpoint of the same name as the model.

    -   The aws_autopilot_create_model call creates a default endpoint
        > configuration with the name \'yourmodelname-m5-4xl-2\', with
        > the following parameters :\"InitialInstanceCount\": 2,
        > \"InstanceType\": \"ml.m5.4xlarge\". Advanced users can go
        > lower or higher depending on their dataset sizes and
        > performance needs. See
        > [[AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG]{.ul}](#create-endpoint-config)
        > for more details on specifying a custom endpoint
        > configuration. (In the above example, the name of the endpoint
        > configuration created would be \'abalonemodel-m5-4xl-2\'. )

    -   Using the above endpoint config, the model will be deployed to
        > an endpoint with the same name as the model (In the above
        > example the endpoint name would be \'abalonemodel\'. The time
        > to live of the endpoint will be 604800 seconds (7 days), after
        > which it is automatically deleted.

    -   If you would like to redeploy the model after it has been
        > deleted, use the
        > [[AWS_AUTOPILOT_CREATE_ENDPOINT]{.ul}](#create-endpoint)
        > command and you can either specify the default endpoint
        > configuration created or specify a custom endpoint
        > configuration.

> **Note**: See
> [[https://aws.amazon.com/sagemaker/pricing/]{.ul}](https://aws.amazon.com/sagemaker/pricing/)
> for details on instance pricing and to estimate costs.

**Option 2:**

Advanced users who would like to specify different default values for
the various optional parameters can use this variation of the
AWS_AUTOPILOT_CREATE_MODEL call.

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_CREATE_MODEL(MODELNAME VARCHAR, TRAINING_TABLE_NAME     |
| VARCHAR, TARGET_COL VARCHAR, OBJECTIVE_METRIC VARCHAR, PROBLEM_TYPE   |
| VARCHAR,MAX_CANDIDATES INTEGER, MAX_RUNNING_TIME INTEGER,             |
| DEPLOY_MODEL BOOLEAN, MODEL_ENDPOINT_TTL INTEGER)                     |
|                                                                       |
| **Arguments:**\                                                       |
| MODELNAME (required) - Name that will be used to refer to the best    |
| model found by Autopilot. Allowed Pattern:                            |
| \^\[a-zA-Z0-9\](-\*\[a-zA-Z0-9\]){0,62}                               |
|                                                                       |
| TRAINING_TABLE_NAME (required) - Name of the table from which to      |
| create the model. All rows will be used to train the model.           |
|                                                                       |
| TARGET_COL (required) - The name of the target column that we want    |
| the model to predict.                                                 |
|                                                                       |
| OBJECTIVE_METRIC (optional) - \"Accuracy\", \"MSE\", \"AUC\", \"F1\", |
| and \"F1macro\". If NULL, Autopilot will auto infer this information. |
|                                                                       |
| PROBLEM_TYPE (optional) - Type of problem: \"Regression\",            |
| \"BinaryClassification\", \"MulticlassClassification\" or \"Auto\".   |
| If NULL the default value will be set to \"Auto\".                    |
|                                                                       |
| MAX_CANDIDATES (optional) - Maximum number of times a training job is |
| allowed to run. Valid values are integers 1 and higher. Can be        |
| leveraged to optimize for speed and have the create model call        |
| complete quicker by limiting the number of candidates explored. If    |
| NULL, Autopilot will auto infer this information. **Note:** For       |
| optimizing for objective_metric we suggest leaving this field unset,  |
| such that the AutoML job can explore all possible candidates and pick |
| the best one.                                                         |
|                                                                       |
| MAX_RUNNING_TIME (optional) - Maximum runtime, in seconds, an AutoML  |
| job has to complete.If NULL the default value will be set to 86000    |
| seconds. **Note:** The parameter is intended to set a timeout on the  |
| length of the training job, and if the job has not finished within    |
| the specified limit it is forcefully stopped and a model will NOT be  |
| created. If you would like to optimize for speed and have a model     |
| successfully created in a shorter duration consider using the         |
| MAX_CANDIDATES parameter.                                             |
|                                                                       |
| DEPLOY_MODEL (optional) - TRUE or FALSE. If NULL the default value    |
| will be TRUE and the best model will be transparently deployed to a   |
| SageMaker Endpoint.\                                                  |
| The default endpoint configuration used is as follows                 |
| :\"InitialInstanceCount\": 2, \"InstanceType\": \"ml.m5.4xlarge\".    |
| Advanced users can go lower or higher depending on their dataset      |
| sizes and performance needs. See                                      |
| [                                                                     |
| [AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG]{.ul}](#create-endpoint-config) |
| for more details on specifying a custom endpoint configuration.       |
|                                                                       |
| MODEL_ENDPOINT_TTL (optional) - Time to live off the model endpoint   |
| in seconds. If NULL the default value will be 7 days.                 |
|                                                                       |
| **Note:** See                                                         |
| [[https://aws.amazon.com                                              |
| /sagemaker/pricing/]{.ul}](https://aws.amazon.com/sagemaker/pricing/) |
| for details on instance pricing and to estimate costs.                |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_create_model (\'abalonemodel\',                  |
| \'abalone_training_dataset\', \'rings\', \'Accuracy\',                |
| \'MulticlassClassification\', 20000, \'True\', 86400 )                |
|                                                                       |
| **Note:** External functions do not support optional parameters. For  |
| the optional arguments which are wished to be skipped should be       |
| specified as a NULL.                                                  |
|                                                                       |
| **Expected output on success:**\                                      |
| \"Model creation in progress. Model ARN =                             |
| ar                                                                    |
| n:aws:sagemaker:us-west-2:631484165566:automl-job/abalonemodel-job.\" |
+=======================================================================+
+-----------------------------------------------------------------------+

### **Describe Model**

> Use the AWS_AUTOPILOT_DESCRIBE_MODEL external function in a SQL query
> to check the status and track progress of your Autopilot training job
> and the model.

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_DESCRIBE_MODEL(MODELNAME VARCHAR)                       |
|                                                                       |
| **Arguments:**\                                                       |
| MODELNAME (required) - Name of the model.                             |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_describe_model (\'abalonemodel\')                |
|                                                                       |
| **The response includes the following information:**                  |
|                                                                       |
| **Job status**: "Completed", "InProgress", "Failed", "Stopped",       |
| "Stopping"                                                            |
|                                                                       |
| **Job status detail**: Starting, AnalyzingData, FeatureEngineering,   |
| ModelTuning,MaxCandidatesReached, Failed, Stopped,                    |
| MaxAutoMLJobRuntimeReached, Stopping, DeployingModel,                 |
| CandidateDefinitionsGenerated                                         |
|                                                                       |
| **Problem type:** "Regression", "BinaryClassification" or             |
| MulticlassClassification".                                            |
|                                                                       |
| **Objective metric:** "Accuracy", "MSE", "AUC", "F1", and "F1macro".  |
|                                                                       |
| **Best Objective Metric Value:** Value of the objective metric for    |
| the best model found so far.                                          |
|                                                                       |
| **Failure reason:** Returns the reason for failure, if the status was |
| "Failed"                                                              |
+=======================================================================+
+-----------------------------------------------------------------------+

### **Predict Outcome**

> Use the AWS_AUTOPILOT_PREDICT_OUTCOME external function in a SQL query
> to make predictions using the ML model produced by Autopilot.

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_PREDICT_OUTCOME(MODEL_ENDPOINT_NAME VARCHAR,COLUMNS     |
| ARRAY)                                                                |
|                                                                       |
| **Arguments:**\                                                       |
| MODEL_ENDPOINT_NAME (required) - Name of the endpoint the model is    |
| deployed to. Note: Unless the model was manually deployed to a custom |
| endpoint this will be the same as the model name.                     |
|                                                                       |
| COLUMNS (required) - Array of values or feature columns to pass as    |
| inputs for model prediction. The ordering should match that of the    |
| training dataset, minus the target column.                            |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_predict_outcome (\'abalonemodel\',               |
| array_construct(\'M\',0.455, 0.365, 0.095, 0.514, 0.2245, 0.101,      |
| 0.15));                                                               |
|                                                                       |
| select aws_autopilot_predict_outcome (\'abalonemodel\',               |
| array_construct(sex, length, diameter, height, whole_weight,          |
| shucked_weight, viscera_weight, shell_weight)                         |
|                                                                       |
| ) as prediction                                                       |
|                                                                       |
| from abalone_test_dataset;                                            |
|                                                                       |
| **Response**:                                                         |
|                                                                       |
| Returns the predicted target value for each row of attributes.        |
+=======================================================================+
+-----------------------------------------------------------------------+

### **Create Endpoint Config**

> Use the AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG external function in a
> SQL query to create an endpoint configuration that Amazon SageMaker
> hosting services use to deploy models.
>
> This allows advanced users to pick a custom endpoint configuration to
> go lower or higher depending on their dataset sizes and performance
> needs compared to the default endpoint configuration used by the
> create model call.

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_CREATE_ENDPOINT_CONFIG(ENDPOINTCONFIG_NAME              |
| VARCHAR,MODELNAME VARCHAR,INSTANCE_TYPE VARCHAR,INSTANCE_COUNT        |
| NUMBER)                                                               |
|                                                                       |
| **Arguments (all are required parameters):**\                         |
| ENDPOINT_CONFIG_NAME- The name of the endpoint configuration. You     |
| specify this name in a CreateEndpoint request. Allowed Pattern:       |
| \^\[a-zA-Z0-9\](-\*\[a-zA-Z0-9\]){0,62}                               |
|                                                                       |
| MODELNAME - The name of the model that you want to host. This is the  |
| name that you specified when creating the model.                      |
|                                                                       |
| INSTANCE_TYPE - The ML compute instance type. See [[SageMaker         |
| instance                                                              |
| types]                                                                |
| {.ul}](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_ |
| ProductionVariant.html#sagemaker-Type-ProductionVariant-InstanceType) |
| for more details.                                                     |
|                                                                       |
| INSTANCE_COUNT - Number of instances to launch.                       |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_create_endpoint_config (                         |
| \'abalone-endpoint-config\',\'abalonemodel\', \'ml.c5d.4xlarge\', 3)  |
+=======================================================================+
+-----------------------------------------------------------------------+

### **Describe Endpoint Config**

> Use the AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG external function in a
> SQL query to get the description of an endpoint configuration that was
> created using the Create Endpoint Config call.

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_DESCRIBE_ENDPOINT_CONFIG(ENDPOINTCONFIG_NAME)           |
|                                                                       |
| **Arguments (all are required parameters):**\                         |
| ENDPOINT_CONFIG_NAME- The name of the endpoint configuration.         |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_describe_endpoint_config                         |
| (\'abalone-endpoint-config\')                                         |
|                                                                       |
| **Response**:                                                         |
|                                                                       |
| ModelName - The name of the model to be hosted.                       |
|                                                                       |
| InstanceCount - Number of instances to launch.                        |
|                                                                       |
| InstanceType - The ML compute instance type.                          |
+=======================================================================+
+-----------------------------------------------------------------------+

### **Delete Endpoint Config**

> Use the AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG external function in a
> SQL query to delete an endpoint configuration. This command deletes
> only the specified configuration. It does not delete endpoints created
> using the configuration.

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_DELETE_ENDPOINT_CONFIG(ENDPOINTCONFIG_NAME)             |
|                                                                       |
| **Arguments (all are required parameters):**\                         |
| ENDPOINT_CONFIG_NAME- The name of the endpoint configuration.         |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_delete_endpoint_config                           |
| (\'abalone-endpoint-config\')                                         |
+=======================================================================+
+-----------------------------------------------------------------------+

### **Create Endpoint**

> Use the AWS_AUTOPILOT_CREATE_ENDPOINT external function in a SQL query
> to create an endpoint using the endpoint configuration specified in
> the request. Amazon SageMaker uses the endpoint to provision resources
> and deploy models.

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_CREATE_ENDPOINT(ENDPOINT_NAME VARCHAR,                  |
| ENDPOINT_CONFIG_NAME VARCHAR,MODEL_ENDPOINT_TTL INTEGER)              |
|                                                                       |
| **Arguments (all are required parameters):**                          |
|                                                                       |
| ENDPOINT_NAME - The name of the endpoint. The exact endpoint name     |
| must be provided during inference.Allowed Pattern:                    |
| \^\[a-zA-Z0-9\](-\*\[a-zA-Z0-9\]){0,62}                               |
|                                                                       |
| ENDPOINT_CONFIG_NAME - The name of the endpoint configuration.        |
|                                                                       |
| **Note:** If you would like to reuse the default endpoint config      |
| created during model creation this would be                           |
| \'yourmodelname-m5-4xl-2\'.                                           |
|                                                                       |
| MODEL_ENDPOINT_TTL (optional) - Time to live off the model endpoint   |
| in seconds. If NULL the default value will be 7 days.                 |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_create_endpoint (\'abalone-endpoint\',           |
| \'abalone-endpoint-config\', 36000)                                   |
+=======================================================================+
+-----------------------------------------------------------------------+

### 

### **Describe Endpoint**

> Use the AWS_AUTOPILOT_DESCRIBE_ENDPOINT external function in a SQL
> query to get the description of an endpoint.

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_DESCRIBE_ENDPOINT(ENDPOINT_NAME VARCHAR)                |
|                                                                       |
| **Arguments (all are required parameters):**                          |
|                                                                       |
| ENDPOINT_NAME - The name of the endpoint.                             |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_describe_endpoint(\'abalone-endpoint\')          |
|                                                                       |
| **Response:**                                                         |
|                                                                       |
| CreationTime - A timestamp that shows when the endpoint was created.  |
|                                                                       |
| EndpointConfigName - The name of the endpoint configuration           |
| associated with this endpoint.                                        |
|                                                                       |
| EndpointStatus - The status of the endpoint. (Valid values:           |
| OutOfService \| Creating \| Updating \| SystemUpdating \| RollingBack |
| \| InService \| Deleting \| Failed)                                   |
|                                                                       |
| FailureReason - If the status of the endpoint is Failed, the reason   |
| why it failed.                                                        |
+=======================================================================+
+-----------------------------------------------------------------------+

### **Delete Endpoint**

> Use the AWS_AUTOPILOT_DELETE_ENDPOINT external function in a SQL query
> to delete an endpoint. Amazon SageMaker frees up all of the resources
> that were deployed when the endpoint was created.

+-----------------------------------------------------------------------+
| **Syntax:**                                                           |
|                                                                       |
| AWS_AUTOPILOT_DELETE_ENDPOINT(ENDPOINT_NAME VARCHAR)                  |
|                                                                       |
| **Arguments (all are required parameters):**                          |
|                                                                       |
| ENDPOINT_NAME - The name of the endpoint.                             |
|                                                                       |
| **Usage:**\                                                           |
| select aws_autopilot_delete_endpoint(\'abalone-endpoint\')            |
+=======================================================================+
+-----------------------------------------------------------------------+

## SageMaker Studio / SageMaker Clarify

[[Amazon SageMaker
Clarify]{.ul}](https://aws.amazon.com/sagemaker/clarify/) provides
machine learning developers with greater visibility into their training
data and models so they can identify and limit bias and explain
predictions. During the model training process, SageMaker Autopilot
automatically creates a notebook (and PDF report) that displays the 10
features with the greatest feature attribution. The notebook is stored
in:

\<s3
bucket>/output/\<model>/documentation/explainability/output/\<training
run>

Additional information about the generated model can be found in Amazon
SageMaker Studio.

## Costs

There is no additional cost for using the provided Snowflake + Amazon
SageMaker Autopilot Integration.

You are responsible for:

-   The cost of the AWS services and Snowflake compute and storage used
    > while running this reference deployment.

The AWS CloudFormation template includes configuration parameters that
you can customize. Some of these settings, such as instance type, affect
the cost of deployment. For cost estimates, see the pricing pages for
each AWS service you use. Prices are subject to change.

**Tip:** After you deploy the template, [create AWS Cost and Usage
Reports](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/billing-reports-gettingstarted-turnonreports.html)
to track AWS costs associated with the integration. These reports
deliver billing metrics to an Amazon Simple Storage Service (Amazon S3)
bucket in your account. They provide cost estimates based on usage
throughout each month and aggregate the data at the end of the month.
For more information about the report, see [What are AWS Cost and Usage
Reports?](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/billing-reports-costusage.html)

## Cleanup

To cleanup the resources created by the integration:

-   Delete any Sagemaker endpoints that were provisioned while using the
    > integration. You can do this by:

    -   Using the [[Delete Endpoint]{.ul}](#delete-endpoint) SQL command
        > from Snowflake or

    -   By opening the Amazon SageMaker console at
        > [[https://console.aws.amazon.com/sagemaker/]{.ul}](https://console.aws.amazon.com/sagemaker/)
        > and deleting the endpoints. Deleting the endpoints also
        > deletes the ML compute instance or instances that support it.

        -   Under Inference, choose Endpoints.

        -   Choose the endpoint that you created, choose Actions, and
            > then choose Delete.

-   Delete any Sagemaker endpoint configurations that were provisioned
    > while using the integration. You can do this by:

    -   Using the [[Delete Endpoint
        > Config]{.ul}](#delete-endpoint-config) SQL command from
        > Snowflake or

    -   By opening the Amazon SageMaker console at
        > [[https://console.aws.amazon.com/sagemaker/]{.ul}](https://console.aws.amazon.com/sagemaker/)
        > and:

        -   Under Inference, choose Endpoint configurations.

        -   Choose the endpoint configurations that you created, choose
            > Actions, and then choose Delete.

-   Delete any Sagemaker Autopilot Models that were created. You can do
    > this by:

    -   By opening the Amazon SageMaker console at
        > [[https://console.aws.amazon.com/sagemaker/]{.ul}](https://console.aws.amazon.com/sagemaker/)
        > and:

        -   Under Inference, choose Models.

        -   Choose the model that you created in the, choose Actions,
            > and then choose Delete.

-   Log in to the AWS console and navigate to CloudFormation service.
    > Select the stack that was created when you deployed the template
    > and click on Delete. This deletes all the AWS resources
    > provisioned by the template, except the S3 bucket. S3 bucket is
    > not automatically deleted as it might contain training data and
    > outputs from the Autopilot jobs.

    -   To delete the S3 bucket, you need to navigate to the S3 service
        > and manually delete the bucket. For more information see
        > [[Deleting a
        > bucket]{.ul}](https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html).

-   Clean up the Snowflake resources by logging into the Snowflake
    > console and

    -   Use the [[DROP
        > INTEGRATION]{.ul}](https://docs.snowflake.com/en/sql-reference/sql/drop-integration.html#drop-integration)
        > SQL command to delete the API and Storage integrations setup.

> Note: You can use the SHOW INTEGRATIONS LIKE \'%AWS_AUTOPILOT% SQL
> command to see the integrations.

-   Use the [[DROP
    > FUNCTION]{.ul}](https://docs.snowflake.com/en/sql-reference/sql/drop-function.html)
    > SQL command to delete the user defined functions that were set up.

> Note: You can use SHOW FUNCTIONS LIKE \'%AWS_AUTOPILOT%\' SQL command
> to see all the functions.
