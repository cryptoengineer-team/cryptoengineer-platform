# Lambda function to create a lambda and an API Gateway to deploy a sklearn model

import json
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os

import logging
from lambda_wrapper import LambdaWrapper
from apigateway_wrapper import APIGatewayWrapper

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

s3_client = boto3.client('s3')
bucket_name = os.environ['BUCKET_NAME']

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

# Función para validar que el modelo y la versión no existe ya para ese usuario
def model_version_exists(username, model_name, model_version):
    try:
        prefix = f"models/{username}/{model_name}/"
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            for obj in response['Contents']:
                parts = obj['Key'].split('/')
                if len(parts) > 3 and parts[3] == model_version:
                    return True
        return False
    except NoCredentialsError:
        logger.error("Credenciales de AWS no encontradas.")
        return False
    except ClientError as e:
        logger.error("Error al verificar la versión del modelo: %s", e)
        return False

def get_pkl_files(bucket_name, folder_prefix):

    # List all objects in the bucket under the given folder/prefix
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)

    # Check if the folder has any objects
    if 'Contents' in response:
        # Loop through the contents and filter out .pkl files
        pkl_files = [item['Key'] for item in response['Contents'] if item['Key'].endswith('.pkl')]

        if pkl_files:
            return pkl_files
        else:
            logger.info("No .pkl files found.")
            #return "No .pkl files found."
    else:
        logger.info("No .pkl files found.")
        pkl_files=[]
    
    return pkl_files

def lambda_handler(event, context):
    # Función lambda que lista los objetos en un bucket de s3 con un prefijo y genera urls prefirmadas para ellos

    if (event['body']) and (event['body'] is not None):
        body = json.loads(event['body'])
        print("Body 1:",body)
        
        #body = event['body']
        # Read the body parameters
        try:
            body= body['body']
            print("Body 2:",body)
            if (body['user']) and (body['user'] is not None):
                username = body['user']
                
            if (body['model']) and (body['model'] is not None):
                model_name = body['model']

            if (body['version']) and (body['version'] is not None):
                model_version = body['version']
                
        except KeyError:
            logger.error("Invalid or incorrect arguments.")
            return {
                'statusCode': 404,
                'body': json.dumps("Invalid or incorrect arguments.")
            }

    # Check if the model and version exists
    if model_version_exists(username, model_name, model_version):
        folder_prefix = f"models/{username}/{model_name}/{model_version}/"
        # Get the model file, a .pkl file.
        pkl_files= get_pkl_files(bucket_name, folder_prefix)
        
        if pkl_files and len(pkl_files)>0:
            model_location=pkl_files[0]
            """
            #iam_role_arn="arn:aws:iam::223817798831:role/service-role/predict_model-role-ynh9ez1d"
            iam_role_arn=os.environ['IAM_ROLE_ARN']
            lambda_name=f"sklearn-{username}-{model_name}"
            lambda_description=f"Return prediction from sklearn model {lambda_name}"
            handler_name="lambda_function.lambda_handler"
            package_type="Image"
            time_out=180
            env_vars={'Variables': {"AWS_BUCKET_NAME": bucket_name,
                                    "AWS_MODEL_KEY": model_location
                                    }
                    }
            
            deployment_package=os.environ['IMAGE_URI']
            # Create a lambda function to make predictions for a sklearn model
            try:
                lambda_arn= create_lambda(iam_role_arn,  lambda_name, lambda_description, handler_name, package_type, deployment_package, time_out, env_vars)       
            except Exception:
                logging.exception("An error ocurred when creating the Lambda Function")
                return {
                    'statusCode': 500,
                    'body': json.dumps("An error ocurred when creating the Lambda Function")
                }
            
            api_name=lambda_name
            
            # Set the AWS resource clients
            apigateway_client = boto3.client("apigateway")
            # Instanciate a Lambda 
            wrapper = APIGatewayWrapper(apigateway_client)
            
            response= wrapper.create_api_deployment(api_name, "1.0", lambda_arn)
            
            return {
                    'statusCode': 200,
                    'body': json.dumps(response)
                }

            """
            return {
                    'statusCode': 200,
                    'body': json.dumps(model_location)
                }

        else:
            return {
                    'statusCode': 404,
                    'body': json.dumps("No .pkl files found.")
                }
    else:
        return {
                'statusCode': 404,
                'body': json.dumps("Model or version not found.")
            }
