#%help

BUCKET = 'cryptoengineer'
#Importación de librerías necesarias
from pyspark.sql.types import StructField, StructType, StringType, DoubleType, IntegerType, TimestampType, DateType
from pyspark.sql.functions import col, from_unixtime, lit, regexp_replace, current_date, min as spark_min, max as spark_max, upper, date_format
import boto3
import os
import sys

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
        sys.argv, ['WORKFLOW_NAME', 'WORKFLOW_RUN_ID', 'type']
    )
    
    print(glue_args)
    
    asset_type = glue_args['type']

else:
    print("Running as Job")
    args = getResolvedOptions(sys.argv,
                              ['JOB_NAME',
                               'type'])

    asset_type = args['type']
#asset_type = 'cryptos'
# Carga las particiones disponibles
partitions_df = spark.read.parquet('s3://' + BUCKET + f'/datalake/bronze/{asset_type}').select('load_date').distinct()

# Encuentra el último load_date
max_load_date = partitions_df.agg(spark_max('load_date')).collect()[0][0]

print(f"Último load_date encontrado: {max_load_date}")
#Definición del esquema
schema = StructType([
    StructField("SYMBOL", StringType(), False),
    StructField("BASE_CURRENCY", StringType(), True),
    StructField("TYPE", StringType(), True),
    StructField("DATETIME", TimestampType(), True),
    StructField("DATE", DateType(), True),
    StructField("TIME", StringType(), True),
    StructField("FREQUENCY", StringType(), True),
    StructField("YEAR", IntegerType(), False),
    StructField("MONTH", IntegerType(), True),
    StructField("DAY", IntegerType(), True),
    StructField("OPEN", DoubleType(), True),
    StructField("HIGH", DoubleType(), True),
    StructField("LOW", DoubleType(), True),
    StructField("CLOSE", DoubleType(), True),
    StructField("VOLUME", DoubleType(), True),
    StructField("TRADES", IntegerType(), True),
    StructField("AUDIT_TIME", DateType(), True)
])
# Leer los datos correspondientes al último load_date
latest_data_df = (
    spark.read
    .schema(schema)
    .parquet('s3://' + BUCKET + f'/datalake/bronze/{asset_type}')
    .filter(col('load_date') == max_load_date)
)

# Verifica la estructura y muestra algunas filas
latest_data_df.printSchema()
latest_data_df.show(5)
#transformo datos para obtener la estructura de silver
transformed_data_df = (
    latest_data_df
    .withColumn('year', col('datetime').substr(0, 4))
    .withColumn('month', col('datetime').substr(6, 2))
    .withColumn('day', col('datetime').substr(9, 2))
    .withColumn('frequency', lit('15min'))
    .withColumn('base_currency', lit('USD'))
    .withColumn("date", date_format(col("datetime"), "yyyy-MM-dd"))
    .withColumn("time", date_format(col("datetime"), "HH:mm:ss"))
    .select(
        col('symbol').alias('SYMBOL'),
        col('base_currency').alias('BASE_CURRENCY'),
        lit(asset_type).alias('TYPE'),
        col('datetime').alias('DATETIME'),
        col('date').alias('DATE'),
        col('time').alias('TIME'),
        col('frequency').alias('FREQUENCY'),
        col('year').cast(IntegerType()).alias('YEAR'),
        col('month').cast(IntegerType()).alias('MONTH'),
        col('day').cast(IntegerType()).alias('DAY'),
        col('open').alias('OPEN'),
        col('high').alias('HIGH'),
        col('low').alias('LOW'),
        col('close').alias('CLOSE'),
        col('volume').alias('VOLUME'),
        col('trades').alias('TRADES'),
        current_date().alias('AUDIT_TIME')
    )
)
transformed_data_df.printSchema()
transformed_data_df.show(5)
#persistimos los datos en la capa silver, reparticionando por simbolo y año, en modalidad append
(
    transformed_data_df
    .write
    .format('parquet')
    .mode("append")
    .partitionBy("SYMBOL", "YEAR")
    .save('s3://' + BUCKET + f'/datalake/silver/{asset_type}')
)

print('Datos guardados en s3://' + BUCKET +  f'/datalake/silver/{asset_type}')
job.commit()