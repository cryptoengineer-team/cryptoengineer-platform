import boto3
import botocore
import sys
import os
import pandas as pd
import pickle
import joblib
import cryptoengineersdk
import datetime

from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from pyspark.context import SparkContext

# Inicializamos el contexto de Glue
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
print("GlueContext inicializado")

args = getResolvedOptions(sys.argv, ['model_location','script_location','model_type','base_currency','symbol', 'frequency'])
# Obtenemos las fechas de inicio y fin desde los parámetros del job de Glue
fec_ini = '2024-01-01 00:00:00' #datetime.datetime.now() # generar la fecha de ejecució
fec_fin = '2024-09-01 00:00:00' #fec_fin - 7   # quitar 7 dias
model = args['model_location']
script = args['script_location']
model_type = args['model_type']
base_currency = args['base_currency']
symbol = args['symbol']
frequency = args['frequency']
print("Parámetros obtenidos")

# script
parts_script = script.split('/')
username = parts_script[4]
script_name = parts_script[5]
script_version = parts_script[6]
script_file_name = parts_script[7]

# Sacamos las variables del modelo
if model != 'empty':
    parts = model.split('/')
    model_file_name = parts[7]
    local_model_path = f'/tmp/{model_file_name}'
    model_key = f'models/{username}/{script_name}/{script_version}/{model_file_name}'

# Parámetros para S3 y el script
bucket_name = 'cryptoengineer'
local_script_path = f'/tmp/script_file.py'
output_key = f'models/{username}/{script_name}/{script_version}/output/output.csv'
script_key = f'models/{username}/{script_name}/{script_version}/{script_file_name}'


# Descargamos el script y el modelo desde S3
s3 = boto3.client('s3')
try:
    s3.download_file(bucket_name, script_key, local_script_path)
    if model != 'empty':
        s3.download_file(bucket_name, model_key, local_model_path)
    print("Script y modelo descargados exitosamente")
except botocore.exceptions.ClientError as e:
    print(f"Error descargando el script o el modelo: {e}")
    sys.exit(1)

# Añadimos el directorio del script al path del sistema
sys.path.insert(0, '/tmp')

# Importamos el script descargado
import script_file
print("Script importado")

# Cargamos el modelo basado en su tipo
if model_type == 'SCRIPTING':
    print("No se usa modelo")
    model = None
elif model_type == 'ML SCKIT-LEARN':
    if model.endswith('.pkl'):
        print("Modelo pickle")
        with open(local_model_path, 'rb') as model_file:
            model = joblib.load(model_file)
    elif model.endswith('.joblib'):
        print("Modelo joblib")
        print(local_model_path)
        print(type(local_model_path))
        model = joblib.load(local_model_path)
    else:
        print("Tipo de modelo no soportado")
        sys.exit(1)

# Llamamos a la función eval_model
result = script_file.eval_model(model, fec_ini, fec_fin)
print("Modelo evaluado")

# Convertimos el resultado en un DataFrame y añadimos las variables del modelo
df = pd.DataFrame(result, columns=['DATETIME', 'CLOSE', 'SIGNAL'])
df['username'] = username
df['model_type'] = model_type
df['model_name'] = script_name
df['model_version'] = script_version
df['symbol'] = symbol
df['frecuency'] = frequency
df['base_currency'] = base_currency
print("DataFrame creado")

# Guardamos el DataFrame como CSV
local_output_path = '/tmp/output.csv'
df.to_csv(local_output_path, index=False)
print("CSV guardado")

# Subimos el CSV a S3
try:
    s3.upload_file(local_output_path, bucket_name, output_key)
except botocore.exceptions.ClientError as e:
    print(f"Error subiendo el CSV: {e}")
    sys.exit(1)

print("Job completado exitosamente.")