import logging
import pprint
import requests
import json
import boto3
from botocore.exceptions import ClientError
# URL de API de tokens
URL_API_TOKEN = "https://q4feu6uy9j.execute-api.us-east-1.amazonaws.com/pro"

logger = logging.getLogger(__name__)


def user_auth(user_token:dict):
    # Función para la validación del usuario, donde llega un usuario y su token, validando que sean correctos

    # Obtenemos el usuario facilitado
    user =user_token['user']
    # Obtenemos el token facilitado
    token = user_token['token']
    # Validamos si son correctos
    response = requests.get(f"{URL_API_TOKEN}/token/{user}/{token}")
    # Si el resultado es "Granted access" devolvemos True, si no, devolvemos False
    if response.content.decode('utf-8').strip("\"") == "Granted access":
        return True
    else:
        return False

# Function to include in SDK
URL_API_DEPLOY = "https://1uxn3ixz7j.execute-api.us-east-2.amazonaws.com/pro"
def deploy(user_token: dict, model_name: str, version:str):
    invokeURL=None
    # Validamos el usuario
    print("Validamos usuario")
    if user_auth(user_token):
        print("Validado usuario")
        # Si el usuario es correcto, llamamos a la función run_test
        # Obtenemos el usuario facilitado
        user = user_token['user']
        # Obtenemos el token facilitado
        token = user_token['token']
        # Creamos el cuerpo del mensaje a enviar con los parametros
        body= {
            "body": {
                "user": user,
                "model": model_name,
                "version": version
            }
        }
        print("Solicitamos creacion de API")
        # Llamamos a la API para que despliegue el modelo
        response= requests.post(f"{URL_API_DEPLOY}/deploy", json=body)
        # Obtenemos la información de la tabla solicitada via API
        #response = requests.get(f"{URL_API_TABLE_INFO}/list_info")
        print("Creacion de API", response)
        invokeURL = json.loads(response.content.decode('utf-8'))
    else:
            # Si la validación de usuario-token no son correctos, devolvemos un mensaje de error
            raise ("You don`t have access to data lake or your credentials are incorrect")
        
    return invokeURL
    
# Function to include in SDK
URL_API_SHUTDOWN = "https://1uxn3ixz7j.execute-api.us-east-2.amazonaws.com/pro"
def shutdown(user_token: dict, url: str):
    # Validamos el usuario
    print("Validamos usuario")
    if user_auth(user_token):
        print("Validado usuario")
        # Si el usuario es correcto, llamamos a la función run_test
        # Obtenemos el usuario facilitado
        user = user_token['user']
        # Obtenemos el token facilitado
        token = user_token['token']
        # Creamos el cuerpo del mensaje a enviar con los parametros
        body= {
            "body": {
                "url": url
            }
        }
        print("Solicitamos la eliminación de API")
        # Llamamos a la API para que despliegue el modelo
        response= requests.post(f"{URL_API_SHUTDOWN}/shutdown", json=body)
        # Obtenemos la información de la tabla solicitada via API
        #response = requests.get(f"{URL_API_TABLE_INFO}/list_info")
        if response.status_code == 200:
            message = json.loads(response.content.decode('utf-8'))
            print(message)
            return True
        else:
            message = json.loads(response.content.decode('utf-8'))
            print(message)
            return False
    else:
            # Si la validación de usuario-token no son correctos, devolvemos un mensaje de error
            raise ("You don`t have access to data lake or your credentials are incorrect")

if __name__ == "__main__":
    """
    user_token = {'user': 'hector', 'token': 'a9agHyfg5478GfufUfj98534fs4gHh89Ig7v6fG89kJy7U5f5FFhjU88'}
    model_name = "skl_iris_predict"
    version = "1"
    invoke_URL=deploy(user_token, model_name, version)
    
    print(invoke_URL)
    """
    #url = "https://oynbvfi8d5.execute-api.us-east-2.amazonaws.com/dev/predict"
    #print(get_api_name(url))
    
    """
    paginator = apigateway_client.get_paginator('get_rest_apis')
    page_iterator = paginator.paginate(PaginationConfig={'MaxItems': 1})

    for page in page_iterator:
        pprint.pp(page)    
    """
"""
aws lambda create-function \
  --function-name test_sklearn_model \
  --package-type Image \
  --code ImageUri=223817798831.dkr.ecr.us-east-2.amazonaws.com/sklearn_model:latest \
  --role arn:aws:iam::223817798831:role/service-role/predict_model-role-ynh9ez1d    
"""