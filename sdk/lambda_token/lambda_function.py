## Recordar que hay que meter la layer de pandas para el awswrangler y actualizar la variables de db y table

import json
import boto3
import awswrangler as wr

def lambda_handler(event, context):
    print("Entra")
    db_name = 'token_db'
    table_name = 'sec_t_tokens'

    # Obtener los parámetros de ruta  
    path_parameters = event.get('pathParameters', {})
    
    # Extraer valores específicos de los parámetros de ruta
    user = path_parameters.get('user')
    token = path_parameters.get('token')
    print(f"user {user} y token {token}")
    
    glue_client = boto3.client('glue')
    
    print("glue")
    response = glue_client.get_table(DatabaseName=f"{db_name}", Name=f"{table_name}")
    location = response['Table']['StorageDescriptor']['Location']
    
    print(location)
    df = wr.s3.read_parquet(location, dataset=True)
    
    print(df)
    
    users_unique = df['user'].unique()
    
    print(users_unique)
    
    if user in users_unique:
        if token == df[df['user'] == user]['token'].values[0]:
            return {
                'statusCode': 200,
                'body': json.dumps('Granted access')
            }
        else:
            return {
                'statusCode': 401,
                'body': json.dumps('Denied access')
            }