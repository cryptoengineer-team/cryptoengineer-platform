#%help
#%stop_session



BUCKET = 'cryptoengineer-lg'

#SYMBOLS = ["Nasdaq", "DowJones", "DAX", "EuroStoxx50", "IBEX35"]
SYMBOLS = ["Nasdaq"]
import sys
import os
import site

# Find the path where bs4 is installed
user_site_packages = site.getusersitepackages()
bs4_path = os.path.join(user_site_packages, "bs4")

# Add the path to sys.path
sys.path.append(bs4_path)

# Try importing bs4 again
try:
    import bs4
    print("bs4 module imported successfully")
except ModuleNotFoundError:
    print("bs4 module not found")
#Importación de librerías necesarias
from pyspark.sql.types import StructField, StructType, StringType, DoubleType, IntegerType, TimestampType, DateType
from pyspark.sql.functions import col, from_unixtime, lit, regexp_replace, current_date, min as spark_min, max as spark_max
import boto3


import InvestingScraper

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
  
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
#Load job parameters
glue_client = boto3.client("glue")

if '--WORKFLOW_NAME' in sys.argv and '--WORKFLOW_RUN_ID' in sys.argv:
    print("Running in Glue Workflow")
    
    glue_args = getResolvedOptions(
        sys.argv, ['WORKFLOW_NAME', 'WORKFLOW_RUN_ID', 'running_mode']
    )
    
    print(glue_args)
    
    running_mode = glue_args['running_mode']

else:
    print("Running as Job")
    args = getResolvedOptions(sys.argv,
                              ['JOB_NAME',
                               'running_mode'])

    running_mode = args['running_mode']
#running_mode = 'daily'
running_mode = 'historic'
#Creación del esquema 
esquema_bronze_df = StructType([
    StructField('TIMESTAMP', StringType(), True),
    StructField('OPEN', DoubleType(), True),
    StructField('HIGH', DoubleType(), True),
    StructField('LOW', DoubleType(), True),
    StructField('CLOSE', DoubleType(), True),
    StructField('VOLUME', DoubleType(), True),
    StructField('TRADES', IntegerType(), True),
    StructField('ORIGIN', StringType(), True),
    StructField('LOAD_DATE', DateType(), True),
    StructField('SYMBOL', StringType(), True),
    StructField('DATETIME', TimestampType(), True),
    StructField('YEAR', IntegerType(), True)
])
from dateutil.relativedelta import relativedelta 
from datetime import datetime

end_date = datetime.now().strftime("%d-%m-%Y")

if running_mode == 'historic':
    print('Cargando datos históricos de los indices')
    start_date = (datetime.now() + relativedelta(years=-3) ).strftime("%d-%m-%Y")

elif running_mode == 'daily':
    print('Cargando datos diarios de los indices')
    start_date = (datetime.now() + relativedelta(days=-1) ).strftime("%d-%m-%Y")
    
print("Start Date:", start_date)
print("End Date:", end_date)
df = InvestingScraper.get_ohlc_data_for_date_range(symbol="Nasdaq", resolution=15, start_date="15-08-2024", end_date="25-08-2024")
print(df)
import pandas as pd

ohlc_df = pd.DataFrame()
for symbol in SYMBOLS:
    print(f"Cargando datos de {symbol}")
    df = InvestingScraper.get_ohlc_data_for_date_range(symbol, 15, start_date, end_date)
    df['symbol'] = symbol
    ohlc_df = pd.concat([ohlc_df, df])

print("Datos cargados correctamente desde Investing")
print(ohlc_df.head())
ohlc_spark_df = spark.createDataFrame(ohlc_df)

ohlc_spark_df = (
    ohlc_spark_df
     # Transformaciones básicas
     .withColumn('origin', lit('ApiOHLC'))
            .withColumn('load_date', lit(current_date()))
            .withColumn('symbol', lit(pair))
            .withColumn('datetime', from_unixtime(col('timestamp')).cast('timestamp'))
            .withColumn('year', col('datetime').substr(0, 4).cast('int'))
)
ohlc_spark_df.printSchema()
ohlc_spark_df.show(5)
#Persistencia de datos
(
    ohlc_df_total
        .write
        .format('parquet')
        #.partitionBy('symbol','year')
        .partitionBy('load_date')
        .mode('overwrite')
        .save('s3://' + BUCKET + '/bronze')
)

print('Datos guardados en s3://' + BUCKET + '/bronze')
#Persistencia de valores resumen cargados
resumen_csv_path = os.path.join(metadata_path, 'resumen.csv')

resumen_df = (
    ohlc_df_totaldd
    .groupBy("symbol")
    .agg(
        spark_min('datetime').alias('min_datetime'),
        spark_max('datetime').alias('max_datetime'),
        spark_min('timestamp').alias('min_timestamp'),
        spark_max('timestamp').alias('max_timestamp')
    )
)

resumen_df.show()

resumen_df.coalesce(1).write.mode("overwrite").csv(resumen_csv_path, header=True)
print(f"Resumen guradado en {resumen_csv_path}")

import requests
import re
import http.client
import json
import pandas as pd
from datetime import datetime
import time
from bs4 import BeautifulSoup

# Mapping symbols to their integer equivalents and associated endpoints
symbol_map = {
    "Nasdaq": "/indices/nq-100-chart",
    "DowJones": "/indices/us-30-chart",
    "DAX": "/indices/germany-30-chart",
    "EuroStoxx50": "/indices/eu-stoxx50-chart",
    "IBEX35": "/indices/spain-35-chart",
    "EurUsd": "/currencies/eur-usd-chart",
    "GbpUsd": "/currencies/gbp-usd-chart",
    "UsdJpy": "/currencies/usd-jpy-chart",
    "AudUsd": "/currencies/aud-usd-chart",
    "EurGbp": "/currencies/eur-gbp-chart",
    "UsdCad": "/currencies/usd-cad-chart",
    "NzdUsd": "/currencies/nzd-usd-chart",
    "EurJpy": "/currencies/eur-jpy-chart",
    "UsdBrl": "/currencies/usd-brl-chart",
    "UsdMxn": "/currencies/usd-mxn-chart"
}


# Function to convert date to Unix timestamp
def date_to_unix(date_str):
    """
    Convierte una cadena de fecha a un timestamp Unix.

    Args:
        date_str (str): Fecha en formato "dd-mm-yyyy".

    Returns:
        int: Timestamp Unix correspondiente a la fecha dada.
    """
    
    return int(datetime.strptime(date_str, "%d-%m-%Y").timestamp())

symbol="Nasdaq"
resolution=15
start_date="01-01-2021"
end_date="01-01-2022"
    

# Retrieve the symbol information
first_endpoint = symbol_map.get(symbol, None)
if first_endpoint is None:
    print("Invalid symbol")


headers_first = {
    "accept": "*/*",
    "accept-language": "es-ES,es;q=0.9",
    "content-type": "text/plain",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Connection": "keep-alive"
}

# Create a session to handle cookies and headers automatically
session = requests.Session()

# Make the first API call
response = session.get(f"https://www.investing.com{first_endpoint}", headers=headers_first)
if response.status_code == 200:
    html_content = response.text
else:
    print("Failed to retrieve data from the first endpoint")
    print(f"Response text: {response.text}")


# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Extract the carrier and time from the iframe src
iframe = soup.find('iframe', src=re.compile(r'tvc4\.investing\.com'))
if iframe:
    src = iframe['src']
    carrier_match = re.search(r'carrier=([\w\d]+)', src)
    time_match = re.search(r'time=([\d]+)', src)
    pair_id_match = re.search(r'pair_ID=(\d+)', src)
    carrier = carrier_match.group(1) if carrier_match else None
    time_value = time_match.group(1) if time_match else None
    pair_id = pair_id_match.group(1) if pair_id_match else None
else:
    print("Iframe not found")

print(carrier, time_value, pair_id)

# Convert dates to Unix timestamps
from_timestamp = date_to_unix(start_date)
to_timestamp = date_to_unix(end_date)

# Prepare to store the data
all_data = []


#current_to_timestamp = min(from_timestamp + 3 * 365 * 24 * 60 * 60, to_timestamp)

# Use the http.client approach to make the second API call
conn = http.client.HTTPSConnection("tvc4.investing.com",port = 443)

headersList = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"

}

payload = ""

# Construct the second endpoint using the carrier and time values
second_endpoint_path = f"/{carrier}/{time_value}/1/1/8/history?symbol={pair_id}&resolution={resolution}&from={from_timestamp}&to={to_timestamp}"

conn.request("GET", second_endpoint_path, payload, headersList)
response = conn.getresponse()
result = response.read()

try:
    # Parse the JSON response
    data = json.loads(result)
except:
    print('Iteration failed, repeating the last loop' )
    print (result)
# Check if data is available
if 't' in data:
    df = pd.DataFrame(data)
    all_data.append(df)

    # Update from_timestamp to the last timestamp received + 1 second to avoid overlaps
    from_timestamp = data['t'][-1] + 1
    time.sleep(5)
    if max(df['t']) >= to_timestamp:
        break
else:
    print("No more data available")
    break

# Concatenate all dataframes
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)

    # Rename and reorder columns
    final_df.columns = ['timestamp', 'close', 'open', 'high', 'low', 'volume', 'volumeopen', 'volumeac', 'status']
    final_df = final_df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    return final_df
else:
    print("No data retrieved")
    return None

    

## Example usage to get last day
df = get_ohlc_data_for_date_range(symbol="Nasdaq", resolution=15, start_date="15-08-2024", end_date="25-08-2024")
print(df)

#
#
## Example usage to get last 3 years
#from dateutil.relativedelta import relativedelta 
#now = datetime.now().strftime("%d-%m-%Y")
#before = (datetime.now() + relativedelta(years=-3) ).strftime("%d-%m-%Y")
#df = get_ohlc_data_for_date_range(symbol="DowJones", resolution=15, start_date=before, end_date=now)
#print(df)
#
#
#symbols_list = ["Nasdaq",
#"DowJones",
#"DAX",
#"EuroStoxx50",
#"IBEX35",
#"EurUsd",
#"GbpUsd",
#"UsdJpy",
#"AudUsd",
#"EurGbp",
#"UsdCad",
#"NzdUsd",
#"EurJpy",
#"UsdBrl",
#"UsdMxn"]
#
#for i in symbols_list:
#    print ('Inicializando ' + i)
#
#    now = datetime.now().strftime("%d-%m-%Y")
#    before = (datetime.now() + relativedelta(years=-3) ).strftime("%d-%m-%Y")
#    df = get_ohlc_data_for_date_range(symbol=i, resolution=15, start_date=before, end_date=now)
#    print(df)
#    time.sleep(5)
job.commit()