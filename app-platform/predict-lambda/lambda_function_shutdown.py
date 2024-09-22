# Lambda function to remove a lambda and an API Gateway created to deploy a sklearn model

import json
import boto3

import logging
from lambda_wrapper import LambdaWrapper
from apigateway_wrapper import APIGatewayWrapper

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

apigateway_client = boto3.client('apigateway')
lambda_client = boto3.client("lambda")
iam_resource = boto3.resource("iam")


def lambda_handler(event, context):
    # Función lambda que lista los objetos en un bucket de s3 con un prefijo y genera urls prefirmadas para ellos

    if (event['body']) and (event['body'] is not None):
        body = json.loads(event['body'])
        #body = event['body']        
        #print("Body 1:",body)

        # Read the body parameters
        try:
            body= body['body']
            #print("Body 2:",body)
            if (body['url']) and (body['url'] is not None):
                url = body['url']
        except KeyError:
            logger.error("Invalid or incorrect arguments.")
            return {
                'statusCode': 404,
                'body': json.dumps("Invalid or incorrect arguments.")
            }
    # Get the name of the API and check if exists
    wrapper = APIGatewayWrapper(apigateway_client)
    try:
        api_id, api_name = wrapper.get_rest_api_name(url)
    except Exception:
        logging.exception("An error ocurred when getting the API Gateway name")
        return {
                'statusCode': 404,
                'body': json.dumps(f"Invalid API Gateway id or it does not exist: {url}")
        }
    
    if api_name:
        # Delete the API Gateway and its resources
        try:
            wrapper.delete_rest_api(api_id)
        except Exception:
            # if error, return a server error
            logging.exception("An error ocurred when deleting the API Gateway")
            return {
                    'statusCode': 500,
                    'body': json.dumps("An error ocurred when deleting the API Gateway")
                }
                        
        # Instanciate a Lambda 
        wrapper = LambdaWrapper(lambda_client, iam_resource)

        #print(f"Looking for function {lambda_name}...")
        logger.info("Looking for function %s...", api_name)
        function = wrapper.get_function(api_name)
        # If lambda function exists
        if function:
            # Delete the lambda function
            try:
                logger.info("Deleting the %s Lambda function.", api_name)
                wrapper.delete_function(api_name)
            except Exception:
                logging.exception("An error ocurred when deleting the Lambda Function")
                return {
                    'statusCode': 500,
                    'body': json.dumps("An error ocurred when deleting the Lambda Function")
                }

            return {
                'statusCode': 200,
                'body': json.dumps("API and Lambda function deleted sucessfully")
            }
        else:
            logger.info("Function %s does not exist.", api_name)
            return {
                'statusCode': 404,
                'body': json.dumps(f"Function {api_name} does not exist.")
            }
    else:
        logger.info("API Gateway not found.")
        return {
                'statusCode': 404,
                'body': json.dumps("API Gateway not found.")
        }
