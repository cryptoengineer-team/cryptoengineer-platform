import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class APIGatewayWrapper:
    def __init__(self, apigateway_client):
        self.apigateway_client = apigateway_client
        self.aws_region = apigateway_client.meta.region_name

    def create_api_deployment(self, api_name: str, version: str, lambda_arn: str, 
                                stage_name: str='dev', path_part: str= 'predict', http_method: str = 'POST'):
    
        #self.apigateway_client = boto3.client('apigateway')
        #aws_region= apigateway_client.meta.region_name
    
        # Deploy the API
        if stage_name == 'dev':
            stage_description = 'Development stage'
        elif stage_name == 'pro':
            stage_description = 'Production stage'
    
        # Create a REST API Gateway
        api_response = self.apigateway_client.create_rest_api(
            name= api_name, #'sklearn_model_predict',
            description='API to call predict method on sklearn model deployed on a lambda function',
            version=version,
            endpointConfiguration={
                'types': ['REGIONAL']
            }
        )
    
        api_id = api_response['id']
        root_resource_id= api_response['rootResourceId']
        logger.info("API Gateway ID %s created.", api_id)
        
        # Create a new resource
        resource_response = self.apigateway_client.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart=path_part,
        )
    
        resource_id = resource_response['id']
        logger.info("Created resource id %s and Path resource id %s", resource_id, resource_response['path'])
        print(resource_response)
    
        # Create a new POST method
        method = self.apigateway_client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType='NONE',  # Change this if you need authorization
        )
        logger.info("Method %s created", method)
    
        # Create a Method Response
        method_response = self.apigateway_client.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode='200'
        )
    
        logger.info("Method Response %s created", method_response)
    
        # Add Lambda integration to the method
        lambda_uri = f"arn:aws:apigateway:{self.aws_region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        integration_response = self.apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='AWS_PROXY',
            integrationHttpMethod=http_method,
            uri= lambda_uri
        )
        logger.info("Lambda integration created: %s", integration_response)
    
        # Create a stage to deploy the API
        deployment_response = self.apigateway_client.create_deployment(
            restApiId=api_id,
            stageName=stage_name,  # Modify this to your desired stage name
            stageDescription=stage_description,
            description=f'Despliegue API {api_name} Method {http_method} Path {path_part}'    
        )
    
        logger.info("Despliegue API %s Method %s Path %s", api_name, http_method, path_part)
        invokeURL= f"https://{api_id}.execute-api.{self.aws_region}.amazonaws.com/{stage_name}/{path_part}"
        
        # Create the Invoke Lambda permission
        lambda_client = boto3.client('lambda')
        acct_id= boto3.client('sts').get_caller_identity()["Account"]
        source_arn = f"arn:aws:execute-api:{self.aws_region}:{acct_id}:{api_id}/*/{http_method}/{path_part}"
        lambda_client.add_permission(FunctionName=lambda_arn, StatementId=f'invoke_{api_id}', 
                Action='lambda:InvokeFunction', Principal='apigateway.amazonaws.com',
                SourceArn=source_arn)
    
        logger.info("Invoke URL:  %s", invokeURL)
        return invokeURL

    def get_rest_api_name(self, url: str):
        # Obtenemos Restapi id de la URL
        api_id = url.split(".")[0].split("//")[1]

        # Obtenemos el nombre de la API con boto3
        try:        
            api_name = self.apigateway_client.get_rest_api(restApiId=api_id)['name']
        except ClientError as e:
            logger.exception("Error al identificar la API: %s", e)
            raise
        
        return api_id, api_name

    def delete_rest_api(self, restapi_id: str):
        # Eliminamos la API con boto3
        try:
            self.apigateway_client.delete_rest_api(restApiId=restapi_id)
        except ClientError as e:
            logger.exception("Error al eliminar la API: %s", e)
            raise
        return True
