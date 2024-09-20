import boto3
import logging
from lambda_wrapper import LambdaWrapper

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_lambda(iam_role_arn, lambda_name, lambda_description, handler_name, package_type, deployment_package, time_out, env_vars):
    """
    Create a Lambda function that deploys a model's predict function on a container .

    :param iam_role_arn: A Boto3 IAM resource arn that execute the lambda.
    :param lambda_name: The name to give resources created for the scenario, such as the
                        IAM role and the Lambda function.
    """
    #logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # Set the AWS resource clients
    lambda_client = boto3.client("lambda")
    iam_resource = boto3.resource("iam")
    # Instanciate a Lambda 
    wrapper = LambdaWrapper(lambda_client, iam_resource)

    #print(f"Looking for function {lambda_name}...")
    logger.info("Looking for function %s...", lambda_name)
    function = wrapper.get_function(lambda_name)
    if function is None:
        # Create a lambda function based on container image
        #print(f"...and creating the {lambda_name} Lambda function.")
        logger.info("...and creating the %s Lambda function.", lambda_name)
        lambda_arn= wrapper.create_function(
            lambda_name, lambda_description, handler_name, iam_role_arn, package_type, deployment_package,
            time_out, env_vars
        )

        return lambda_arn
    else:
        #print(f"Function {lambda_name} already exists.")
        logger.info("Function %s already exists.", lambda_name)
        return None

#httpMethod='POST'

def create_model_deployment(api_name: str, version: str, lambda_arn: str, 
                            stage_name: str='dev', path_part: str= 'predict', http_method: str = 'POST'):

    apigateway_client = boto3.client('apigateway')
    aws_region= apigateway_client.meta.region_name

    # Deploy the API
    if stage_name == 'dev':
        stage_description = 'Development stage'
    elif stage_name == 'pro':
        stage_description = 'Production stage'

    # Create a REST API Gateway
    api_response = apigateway_client.create_rest_api(
        name= api_name, #'sklearn_model_predict',
        description='API to call predict method on sklearn model deployed on a lambda function',
        version=version,
        endpointConfiguration={
            'types': ['REGIONAL']
        }
    )

    api_id = api_response['id']
    root_resource_id= api_response['rootResourceId']
    #print("API Gateway ID:", api_id)
    logger.info("API Gateway ID %s created.", api_id)
    print("Rest API:", api_response)

    # Create a new resource
    resource_response = apigateway_client.create_resource(
        restApiId=api_id,
        parentId=root_resource_id,
        pathPart=path_part,
    )

    resource_id = resource_response['id']
    #print("Created resource id: ", resource_id)
    #print("Path resource id: ", resource_response['path'])
    logger.info("Created resource id %s and Path resource id %s", resource_id, resource_response['path'])
    print(resource_response)

    # Create a new POST method
    method = apigateway_client.put_method(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod=http_method,
        authorizationType='NONE',  # Change this if you need authorization
    )
    #print("Method created")
    #print("Method response: ", method)
    logger.info("Method %s created", method)
    print(method)

    # Create a Method Response
    method_response = apigateway_client.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode='200'
    )

    #print("Method response created: ", result)
    logger.info("Method Response %s created", method_response)

    # Add Lambda integration to the method
    lambda_uri = f"arn:aws:apigateway:{aws_region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    integration_response = apigateway_client.put_integration(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod=http_method,
        type='AWS_PROXY',
        integrationHttpMethod=http_method,
        uri= lambda_uri
        #"arn:aws:apigateway:us-east-2:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-2:223817798831:function:test_model/invocations"
        #arn:aws:apigateway:{aws-region}:lambda:path/2015-03-31/functions/[lambda_arn]}/invocations
        #arn:aws:apigateway:{aws-region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{aws-region}:{aws-acct-id}:function:{your-lambda-function-name}/invocations
    )
    print("Lambda integration created")
    logger.info("Lambda integration created: %s", integration_response)
    print(integration_response)

    # Create a stage to deploy the API
    deployment_response = apigateway_client.create_deployment(
        restApiId=api_id,
        stageName=stage_name,  # Modify this to your desired stage name
        stageDescription=stage_description,
        description=f'Despliegue API {api_name} Method {http_method} Path {path_part}'    
    )
    #print("API Gateway deplolyed")
    logger.info("Despliegue API %s Method %s Path %s", api_name, http_method, path_part)

    #api_id="9fylkob4j7"
    invokeURL= f"https://{api_id}.execute-api.{aws_region}.amazonaws.com/{stage_name}/{path_part}"
    
    # Create the Invoke Lambda permission
    lambda_client = boto3.client('lambda')
    acct_id= boto3.client('sts').get_caller_identity()["Account"]
    #source_arn = 'arn:aws:execute-api:us-east-2:223817798831:9fylkob4j7/*/POST/predict'
    source_arn = f"arn:aws:execute-api:{aws_region}:{acct_id}:{api_id}/*/{http_method}/{path_part}"
    lambda_client.add_permission(FunctionName=lambda_arn, StatementId=f'invoke_{api_id}', 
            Action='lambda:InvokeFunction', Principal='apigateway.amazonaws.com',
            SourceArn=source_arn)

    #print("Invoke URL: ", invokeURL)
    logger.infologger.info("Invoke URL:  %s", invokeURL)
    return invokeURL


if __name__ == "__main__":
    """
    # Create a lambda function
    iam_role_arn="arn:aws:iam::223817798831:role/service-role/predict_model-role-ynh9ez1d"
    lambda_name="sklearn_model_predict"
    lambda_description="Return prediction from a sklearn model - Test"
    handler_name="lambda_function.lambda_handler"
    package_type="Image"
    time_out=180
    env_vars={'Variables': {"AWS_BUCKET_NAME": "cryptoengineer-app",
                            "AWS_MODEL_KEY": "mlflow/2/cf5d04ca121b4ffea859fd4816e440b1/artifacts/east2_model/model.pkl"
                            }
              }
    
    deployment_package="223817798831.dkr.ecr.us-east-2.amazonaws.com/sklearn_model:latest"
                        #"223817798831.dkr.ecr.us-east-2.amazonaws.com/sklearn_model@sha256:c8a0ec9666634f6089f895b13a7dfc45fd8d03508c392fcba8661ee9f04563f5"
        
    try:
        lambda_arn= create_lambda(iam_role_arn,  lambda_name, lambda_description, handler_name, package_type, deployment_package, time_out, env_vars)       
    except Exception:
        logging.exception("An error ocurred when creating the Lambda Function")
    """

    lambda_arn="arn:aws:lambda:us-east-2:223817798831:function:sklearn_model_predict"

    response= create_model_deployment("sklearn_model_predict_test", "1.0", lambda_arn)
    print("Response Deployment": response)