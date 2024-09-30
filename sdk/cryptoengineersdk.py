import requests
from io import BytesIO
import pandas as pd
import json

# URL de API de accesos al dato
URL_API_DATA = "https://q4feu6uy9j.execute-api.us-east-1.amazonaws.com/pro"
# URL de API de tokens
URL_API_TOKEN = "https://q4feu6uy9j.execute-api.us-east-1.amazonaws.com/pro"
# URL de API de tabla información
URL_API_TABLE_INFO = "https://q4feu6uy9j.execute-api.us-east-1.amazonaws.com/pro"
# URL de API para deploy de un modelo
URL_API_DEPLOY = "https://vcp8tck072.execute-api.us-east-1.amazonaws.com/pro"
# URL de API para eliminar un modelo desplegado
URL_API_SHUTDOWN = "https://vcp8tck072.execute-api.us-east-1.amazonaws.com/pro"


def reader (user_token: dict, table_name: str, symbol:str ='ALL_SYMBOLS', from_year:int = 0, to_year:int = 9999):
    """
    Función para la lectura de symbols del data lake.

    Args:
        user_token (dict): Diccionario con el usuario y su token.
        table_name (str): Nombre de la tabla de la cual se desean leer los datos.
        symbol (str, opcional): Símbolo específico a leer. Por defecto es 'ALL_SYMBOLS'. NO PUEDE SER LISTA.
        from_year (int, opcional): Año inicial para la lectura de datos. Por defecto es 0.
        to_year (int, opcional): Año final para la lectura de datos. Por defecto es 9999.

    Returns:
        dataframe: Dataframe con los valores de los symbolos solicitados.
    """
    # Función para la lectura de datos, donde llega un usuario y su token, y se solicita la lectura de datos

    if from_year > to_year:
        return f"The years are incorrect. The 'from_year' {from_year} must be equal or less than 'to_year' {to_year}. Please check the years."

    # Validamos que los datos facilitados sean correctos
    response = check_params(user_token, table_name, symbol, from_year, to_year)

    if response[0]==False:
            return {
                'statusCode': 400,
                'body': json.dumps(response.content)
            }
    # Validamos si el usuario-token son correctos
    else:
        # Si son correctos, continuamos para la lectura

        # Guardo los symbols y años a listar
        list_symbols_years = response[1]

        dataframes =[]
        for symbol_s, from_year_s, to_year_s in list_symbols_years:

            # Recorremos todos los años para crear los folder prefix
            while from_year_s <= to_year_s:
                # Obtenemos los datos de la tabla solicitada via API
                response = requests.get(f"{URL_API_DATA}/reader/{table_name}/{symbol_s}/{from_year_s}/{from_year_s}")
                data_urls = json.loads(response.content.decode('utf-8'))

                # Leemos lo devuelto por el api, para recorrer objeto por objeto y leer los datos de la url prefirmada
                for url_presigned in data_urls:
                    # Obtenemos el objeto y la url prefirmada
                    object_key = url_presigned[0]
                    url = url_presigned[1]
                    # Si hay url, leemos el parquet de la url y lo añadimos a la lista de dataframes
                    if url:
                        df = read_parquet_from_url(url, object_key)
                        dataframes.append(df)
                print(f"Cargado de {table_name} el symbol {symbol_s} del año {from_year_s}")
                # Incrementar el año
                from_year_s += 1

        if dataframes != []:
            # Devolvemos el dataframe solicitado, concantenando todos los dataframes leídos
            return pd.concat(dataframes, ignore_index=True)
        else:
            # Devolvemos un dataframe vacío
            print(f"No data found for your request")
            return pd.DataFrame()


def get_info(user_token: dict):
    """
    Función para obtener información de los symbols disponibles para leer.

    Args:
        user_token (dict): Diccionario con el usuario y su token.

    Returns:
        dataframe: Dataframe con la información de los datos disponibles para leer con la función reader.
    """
    # Función para la obtención de información de la tabla, donde llega un usuario y su token, y se solicita la información de la tabla

    # Validamos si el usuario-token son correctos
    if user_auth(user_token):
        # Si son correctos, mostramos que el usuario ha sido autenticado
        print(f"{user_token['user']} was authenticated")
    else:
            # Si la validación de usuario-token no son correctos, devolvemos un mensaje de error
            raise ("You don`t have access to data lake or your credentials are incorrect")

    # Obtenemos la información de la tabla solicitada via API
    response = requests.get(f"{URL_API_TABLE_INFO}/list_info")
    data_urls = json.loads(response.content.decode('utf-8'))

    # Leemos lo devuelto por el api, para recorrer objeto por objeto y leer los datos de la url prefirmada
    dataframes =[]
    for url_presigned in data_urls:
        # Obtenemos el objeto y la url prefirmada
        object_key = url_presigned[0]
        url = url_presigned[1]
        # Si hay url, leemos el parquet de la url y lo añadimos a la lista de dataframes
        if url:
            df = read_parquet_from_url(url, object_key)
            dataframes.append(df)

    if dataframes != []:
        # Devolvemos el dataframe solicitado, concantenando todos los dataframes leídos
        return pd.concat(dataframes, ignore_index=True)
    else:
        # Devolvemos un dataframe vacío
        print(f"No data found for your request")
        return pd.DataFrame()
    

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


def read_parquet_from_url(url, object_key):
    # Función para la lectura de un parquet desde una url, devolviendo un dataframe

    # Obtenemos la respuesta de la url
    response = requests.get(url)

    if response.status_code == 200:
        # Obtenemos el contenido de la respuesta y lo leemos con pandas
        response_data = BytesIO(response.content)
        df_url = pd.read_parquet(response_data)
        # Obtenemos las particiones de la tabla
        list_partitions = obtain_partitions_from_object_key(object_key)
        # Si hay particiones, las añadimos al dataframe
        if list_partitions != []:
            for partition in list_partitions:
                df_url[partition[0]] = partition[1]
        # Devolvemos el dataframe
        return df_url
    else:
        print(f"Failed to read {url}")
        return pd.DataFrame()


def obtain_partitions_from_object_key(object_key):
    # Función para la obtención de las particiones de una tabla a partir de un object_key
    list_part = [x.split("=") for x in object_key.split('/') if '=' in x and x != object_key.split('/')[-1]]

    return (list_part)

def check_params(user_token, table_name, symbol, from_year, to_year):
    # Validamos que los parámetros sean correctos
    
    # Obtenemos la información de los datos disponibles
    df_info = get_info(user_token)
    
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

def deploy(user_token: dict, model_name: str, version:str):
    """
    Función para desplegar un modelo scikit-learn subido por el usuario.

    Args:
        user_token (dict): Diccionario con el usuario y su token.
        model_name (str): Nombre del modelo a desplegar.
        version (str): Versión del modelo a desplegar.

    Returns:
        str: URL para invocar el modelo desplegado.
    """
    invokeURL=None
    # Validamos el usuario
    if user_auth(user_token):
        print(f"{user_token['user']} was authenticated")
        # Si el usuario es correcto, llamamos a la función run_test
        # Obtenemos el usuario facilitado
        user = user_token['user']
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
        print("Creacion de API", response)
        invokeURL = json.loads(response.content.decode('utf-8'))
    else:
            # Si la validación de usuario-token no son correctos, devolvemos un mensaje de error
            raise ("You don`t have access to data lake or your credentials are incorrect")
        
    return invokeURL

def shutdown(user_token: dict, url: str):
    """
    Función para eliminar un modelo scikit-learn desplegado por el usuario.

    Args:
        user_token (dict): Diccionario con el usuario y su token.
        url (str): URL de invocación al modelo que deseamos eliminar.

    Returns:
        boolean: True si la operación ha sido correcta.
    """
    
    # Validamos el usuario
    if user_auth(user_token):
        print(f"{user_token['user']} was authenticated")
        # Creamos el cuerpo del mensaje a enviar con los parametros
        body= {
            "body": {
                "url": url
            }
        }
        print("Solicitamos la eliminación de API")
        # Llamamos a la API para que elimine el modelo
        response= requests.post(f"{URL_API_SHUTDOWN}/shutdown", json=body)
        # Comprobamos la validez de la operación
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
