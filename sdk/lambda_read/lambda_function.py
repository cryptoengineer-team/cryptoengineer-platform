# cambiar tiempo timeout de 3sg a 15 min y poner la bbdd que sera fija

import json
import boto3
import awswrangler as wr


def check_params(table_name, symbol, from_year, to_year):
    # Validamos que los parámetros sean correctos
    
    # Variables de la bbdd y la tabla de información
    db_name_t_info = 'cryptoengineer_db'
    table_name_t_info = 'gold_t_info'

    # Creamos cliente de glue
    glue_client = boto3.client('glue')
    # Obtengo donde esta en s3 la tabla T_INFO
    response = glue_client.get_table(DatabaseName=f"{db_name_t_info}", Name=f"{table_name_t_info}")
    location = response['Table']['StorageDescriptor']['Location']

    # Leemos la tabla de información
    df_info = wr.s3.read_parquet(location, dataset=True)
    
    # Validamos que la tabla sea correcta
    if table_name not in df_info['TABLE'].unique():
        return [False, f"The table {table_name} is incorrect. Please check the table in function 'get_info'."]
    
    # cargamos solamente la df_info de la tabla indicada
    df_info_table = df_info[df_info['TABLE']==table_name]
    
    # Si ha pedido todos los symbols, generamos una lista con todos los symbols, validando tambien que las fechas sean correctas. Si estan fuera de rango las ajustamos
    list_symbols_years = []
    if symbol == 'ALL_SYMBOLS':

        if from_year > df_info_table['END_DATETIME'].max().year:
            return [False, f"The 'from_year' {from_year} must be less than 'END_DATETIME' {df_info_table['END_DATETIME'].max().year}. Please check the years."]
        elif to_year < df_info_table['INIT_DATETIME'].min().year:
            return [False, f"The 'to_year' {to_year} must be greater than 'INIT_DATETIME' {df_info_table['INIT_DATETIME'].min().year}. Please check the years."]
        else:
            for symbol in df_info_table['SYMBOL'].unique():
                if to_year > df_info_table[df_info_table['SYMBOL'] == symbol]['END_DATETIME'].max().year:
                    end_year = df_info_table[df_info_table['SYMBOL'] == symbol]['END_DATETIME'].max().year
                else:
                    end_year = to_year
                if from_year < df_info_table[df_info_table['SYMBOL'] == symbol]['INIT_DATETIME'].min().year:
                    init_year = df_info_table[df_info_table['SYMBOL'] == symbol]['INIT_DATETIME'].min().year
                else:
                    init_year = from_year
                list_symbols_years.append([symbol, int(init_year), int(end_year)])
                
    # Validamos que si no son todos los symbols, que el symbol indicado sea correcto
    elif symbol not in df_info_table['SYMBOL'].unique():
        return [False, f"The symbol {symbol} is incorrect. Please check the symbol with function get_info."]
        
    # Si no ha pedido todos los symbols, generamos una lista con el symbol, validando que tambien las fechas sean correctas. Si esta fuera de rango las ajustamos
    else:
        if from_year > df_info_table[df_info_table['SYMBOL'] == symbol]['END_DATETIME'].max().year:
            return [False, f"The 'from_year' {from_year} must be less than 'END_DATETIME' {df_info_table[df_info_table['SYMBOL'] == symbol]['END_DATETIME'].max().year}. Please check the years."]
        elif to_year < df_info_table[df_info_table['SYMBOL'] == symbol]['INIT_DATETIME'].max().year:
            return [False, f"The 'to_year' {to_year} must be greater than 'INIT_DATETIME' {df_info_table[df_info_table['SYMBOL'] == symbol]['INIT_DATETIME'].max().year}. Please check the years."]
        else:
            if to_year > df_info_table[df_info_table['SYMBOL'] == symbol]['END_DATETIME'].max().year:
                end_year = df_info_table[df_info_table['SYMBOL'] == symbol]['END_DATETIME'].max().year
            else:
                end_year = to_year
            if from_year < df_info_table[df_info_table['SYMBOL'] == symbol]['INIT_DATETIME'].min().year:
                init_year = df_info_table[df_info_table['SYMBOL'] == symbol]['INIT_DATETIME'].min().year
            else:
                init_year = from_year
            list_symbols_years.append([symbol, int(init_year), int(end_year)])

    return [True, list_symbols_years]

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
    # Función lambda que lista los objetos en un bucket de s3 con un prefijo y genera urls prefirmadas para ellos
    
    # Extraer valores de los parámetros
    path_parameters = event.get('pathParameters', {})

    table_name = path_parameters.get('table')
    symbol = path_parameters.get('symbol')
    from_year = int(path_parameters.get('from_year'))
    to_year = int(path_parameters.get('to_year'))

    # Variables fijas
    db_name = 'cryptoengineer_db'

    # Validamos que los parámetros sean correctos
    response = check_params(table_name, symbol, from_year, to_year)
    # Compruebo si el check fue correcto
    check_bool = response[0]
    if check_bool==False:
        error=response[1]
        return {
            'statusCode': 400,
            'body': json.dumps(error)
        }
    # Guardo los symbols y años a listar
    list_symbols_years = response[1]
    
    #Inicializamos cliente glue
    glue_client = boto3.client('glue')

    try:
        # Obtengo donde esta en s3 la tabla almacenada
        response = glue_client.get_table(DatabaseName=f"{db_name}", Name=f"{table_name}")
        location = response['Table']['StorageDescriptor']['Location']

    except Exception as e:
        # Si la tabla no existe lo informamos al usuario
        if e.response['Error']['Code'] == 'EntityNotFoundException':
            return {
                'statusCode': 404,
                'body': json.dumps(f"Table not found. Please confirm the table with function 'get_info' and filter the column 'resources'='Table'")
            }
            
    # Obtenemos el nombre del bucket y el prefix

    bucket_name = location.split('/')[2]
    folder_prefix = '/'.join(location.split('/')[3:])

    list_key_url = []
    # Recorremos todos los symbols y años a listar para crear los folder prefix
    for symbol_s, from_year_s, to_year_s in list_symbols_years:

        # Recorremos todos los años para crear los folder prefix
        while from_year_s <= to_year_s:

            # Generamos el folder prefix
            folder_prefix_symbol = f"{folder_prefix}SYMBOL={symbol_s}/YEAR={from_year_s}"

            # Obtenemos lista de todos los objetos en el prefix generado
            object_keys = list_objects_in_bucket(bucket_name, folder_prefix_symbol)

            # voy a guardar un listado de keys de objetos y sus url prefirmadas que será lo que se devuelva al usuario
            for object_key in object_keys:
                # obtengo el key del objeto y su url prefirmada
                try:
                    url_presigned = generate_presigned_url(bucket_name, object_key)
                except:
                    return {
                        'statusCode': 400,
                        'body': "Error en generación de descarga"
                    }
                key = [ object_key , url_presigned]
                # Agrego a la lista de key y url prefirmadas
                list_key_url.append(key)
            
            # Aumentamos un año
            from_year_s += 1

    # Devolvemos la lista de keys y urls prefirmadas a la libreria
    return {
        'statusCode': 200,
        'body': json.dumps(list_key_url)
    }

