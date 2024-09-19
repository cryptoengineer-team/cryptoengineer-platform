# cambiar tiempo de timeout de 3sg a 15min y adaptar las variables fijas de bbdd, nombre tabla info y expiration

import json
import boto3
import awswrangler as wr


def generate_presigned_url(bucket_name, object_name):
    # Genera una url prefirmada para un objeto en un bucket de s3
    
    # Vaeiable fija expiration
    expiration = 900

    # generamos cliente de s3
    s3_client = boto3.client('s3')

    # generamos url prefirmada del key
    response = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket_name,
            'Key': object_name},
        ExpiresIn=expiration
        )
    # devolvemos la url prefirmada
    return response


def list_objects_in_bucket(bucket_name, prefix):
    # Lista los objetos en un bucket de s3 con un prefijo

    # creamos cliente s3
    s3_client = boto3.client('s3')
    # listamos todos los objetos del prefijo
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    # devolvemos la lista de keys de los objetos listados
    return [content['Key'] for content in response.get('Contents', [])]


def lambda_handler(event, context):
    
    # Variables fijas
    db_name = 'cryptoengineer_db'
    table_name = 'gold_t_info'
    
    # Creamos cliente glue
    glue_client = boto3.client('glue')
    
    try:
        # Obtengo donde esta en s3 la tabla almacenada
        response = glue_client.get_table(DatabaseName=f"{db_name}", Name=f"{table_name}")
        location = response['Table']['StorageDescriptor']['Location']

    except Exception as e:
        # Si la tabla no existe lo informamos al usuario
        return {
            'statusCode': 404,
            'body': json.dumps(f"Table not found.")
        }
    # Obtenemos el nombre del bucket y el prefix
    bucket_name = location.split('/')[2]
    folder_prefix = '/'.join(location.split('/')[3:])
    
    list_key_url = []
    # Obtenemos lista de todos los objetos en el prefix generado
    object_keys = list_objects_in_bucket(bucket_name, folder_prefix)
    
    # voy a guardar un listado de keys de objetos y sus url prefirmadas que será lo que se devuelva al usuario
    for object_key in object_keys:
        # obtengo el key del objeto y su url prefirmada
        key = [ object_key , generate_presigned_url(bucket_name, object_key)]
        # Agrego a la lista de key y url prefirmadas
        list_key_url.append(key)

    
    # Devolvemos la lista de keys y urls prefirmadas a la libreria
    return {
        'statusCode': 200,
        'body': json.dumps(list_key_url)
    }
