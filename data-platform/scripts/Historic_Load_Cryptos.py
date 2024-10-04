#%help

BUCKET = 'cryptoengineer'
#Importación de librerías necesarias
from pyspark.sql.types import StructField, StructType, StringType, DoubleType, IntegerType, TimestampType, DateType
from pyspark.sql.functions import col, from_unixtime, lit, regexp_replace, current_date, min as spark_min, max as spark_max
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import boto3
import os

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
#Defino función para determinar los ficheros a procesar
def list_s3_files(bucket_name, folder_prefix):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=folder_prefix)
    
    files = []
    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                # Check if the object is a file and not a directory
                if not obj['Key'].endswith('/'):
                    # Extract the file name from the full S3 key
                    file_name = os.path.basename(obj['Key'])
                    files.append(file_name)
    return files
#Lectura de ficheros CSV a procesar
files = list_s3_files(BUCKET, 'datalake/historic_data/cryptos')

print('Los ficheros a procesar son: ')
for file in files:
    print(file)
#Creación del esquema 
historic_schema = StructType([
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

#Creación del DF de destino
historic_df = spark.createDataFrame([], historic_schema)
#Iteración a través de todos los ficheros 
for file in files:
    print('Procesado el fichero: ' + file)
    #Lectura del fichero
    file_df = (
        spark.read
        .format("csv")
        .schema(historic_schema)
        .option('header', 'false')
        .load('s3://' + BUCKET + '/datalake/historic_data/cryptos/' + file)

        #Transformaciones básicas
        .withColumn('origin', lit('historic'))
        .withColumn('load_date', current_date())
        .withColumn('symbol', regexp_replace(lit(file), '_15.csv', ''))
        .withColumn('datetime', from_unixtime(col('timestamp')).cast('timestamp'))
        .withColumn('year', col('datetime').substr(0, 4).cast('int'))

    )
    historic_df = historic_df.unionAll(file_df)
historic_df.printSchema()
historic_df.show(5)
#Persistencia de datos
(
    historic_df
        .write
        .format('parquet')
        #.partitionBy('symbol','year')
        .partitionBy('LOAD_DATE')
        .mode('append')
        .save('s3://' + BUCKET + '/datalake/bronze/cryptos')
)

print('Datos guardados en s3://' + BUCKET + '/datalake/bronze/cryptos')
job.commit()