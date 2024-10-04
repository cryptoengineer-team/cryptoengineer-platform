

BUCKET = 'cryptoengineer'
#Importación de librerías necesarias
from pyspark.sql.types import StructField, StructType, StringType, DoubleType, IntegerType, TimestampType, DateType
from pyspark.sql.functions import col, from_unixtime, lit, regexp_replace, current_date, min as spark_min, max as spark_max, date_format, datediff
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import boto3
import os
from datetime import datetime

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
#Llevo a cabo la lectura del resumen generado como metadatos en la capa gold con stage igual a bronze
silver_df = (
    spark.read
    .format('parquet')
    .option('header', 'true')
    .load('s3://' + BUCKET + f'/datalake/silver/cryptos')
)

silver_df.printSchema()
silver_df.show(5)
print(f"Count of rows in silver_df: {silver_df.count()}")
wrong_date = '2024-03-31'
audit_time = '2024-09-21'
filtered_df = silver_df.filter((col("AUDIT_TIME") == audit_time) & (col("DATE") == wrong_date))

filtered_df.printSchema()
filtered_df.show(5)
print(f"Count of rows in silver_df: {filtered_df.count()}")
complementary_df = silver_df.subtract(filtered_df)
complementary_df.printSchema()
complementary_df.show(5)
print(f"Count of rows in complementary_df: {complementary_df.count()}")
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
#Lets get sure that the resultant complementary_df has the same types defined in the schema
complementary_df_casted = complementary_df.select(
    
     col('BASE_CURRENCY').cast(schema['BASE_CURRENCY'].dataType),
     col('TYPE').cast(schema['TYPE'].dataType),
     col('DATETIME').cast(schema['DATETIME'].dataType),
     col('DATE').cast(schema['DATE'].dataType),
     col('TIME').cast(schema['TIME'].dataType),
     col('FREQUENCY').cast(schema['FREQUENCY'].dataType),
     col('MONTH').cast(schema['MONTH'].dataType),
     col('DAY').cast(schema['DAY'].dataType),
     col('OPEN').cast(schema['OPEN'].dataType),
     col('HIGH').cast(schema['HIGH'].dataType),
     col('LOW').cast(schema['LOW'].dataType),
     col('CLOSE').cast(schema['CLOSE'].dataType),
     col('VOLUME').cast(schema['VOLUME'].dataType),
     col('TRADES').cast(schema['TRADES'].dataType),
     col('AUDIT_TIME').cast(schema['AUDIT_TIME'].dataType),
     col('SYMBOL').cast(schema['SYMBOL'].dataType),
     col('YEAR').cast(schema['YEAR'].dataType),
)
complementary_df_casted.show()
complementary_df.printSchema()
#persistimos los datos en la capa silver, reparticionando por simbolo y año, en modalidad overwrite
(
    complementary_df
    .write
    .format('parquet')
    .mode("overwrite")
    .partitionBy("SYMBOL", "YEAR")
    .save('s3://' + BUCKET + f'/datalake/silver/cryptos2')
)

print('Datos guardados en s3://' + BUCKET +  f'/datalake/silver/cryptos2')
silver_df2 = (
    spark.read
    .format('parquet')
    .option('header', 'true')
    .load('s3://' + BUCKET + f'/datalake/silver/cryptos2')
)

silver_df.printSchema()
silver_df.show(5)
print(f"Count of rows in silver_df: {silver_df.count()}")
#persistimos los datos en la capa silver, reparticionando por simbolo y año, en modalidad overwrite
(
    silver_df2
    .write
    .format('parquet')
    .mode("overwrite")
    .partitionBy("SYMBOL", "YEAR")
    .save('s3://' + BUCKET + f'/datalake/silver/cryptos')
)

print('Datos guardados en s3://' + BUCKET +  f'/datalake/silver/cryptos')
job.commit()