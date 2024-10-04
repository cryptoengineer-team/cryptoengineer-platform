#%help
#%stop_session



BUCKET = 'cryptoengineer-lg'
#Importación de librerías necesarias
from pyspark.sql.types import StructField, StructType, StringType, DoubleType, IntegerType, TimestampType, DateType
from pyspark.sql.functions import col, from_unixtime, lit, regexp_replace, current_date, min as spark_min, max as spark_max, date_format, datediff
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import boto3
import os
from datetime import datetime
import KrakenApiTrades, KrakenApiOHLC

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
#Llevo a cabo la lectura del resumen generado como metadatos en la capa gold con stage igual a bronze
resumen_bronze_df = (
    spark.read
    .format('parquet')
    .option('header', 'true')
    .load('s3://' + BUCKET + f'/datalake/gold/cryptos')
    .filter(col('STAGE') == 'bronze')
    .filter(col('TYPE') == 'cryptos')
    #.select('symbol', 'datetime', 'timestamp')
    .withColumn('END_DATE_STRING', date_format(col('END_DATETIME'), 'dd-MM-yyyy'))
    .withColumn('CURRENT_DATE_STRING', date_format(current_date(), 'dd-MM-yyyy'))
)

resumen_bronze_df.printSchema()
resumen_bronze_df.show(5)
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

ohlc_df_total = spark.createDataFrame([], esquema_bronze_df)

# Recopilamos las filas del DataFrame
rows = resumen_bronze_df.collect()

for row in rows:
    # Asignamos el valor de END_DATE_STRING a start_date
    start_date = row['END_DATE_STRING']
    
    # Asignamos el valor de CURRENT_DATE_STRING a end_date
    end_date = row['CURRENT_DATE_STRING']
    
    # Convertimos las fechas de cadena a objeto datetime para calcular la diferencia
    start_date_dt = datetime.strptime(start_date, '%d-%m-%Y')
    end_date_dt = datetime.strptime(end_date, '%d-%m-%Y')
    
    # Calculamos la diferencia en días
    delta = (end_date_dt - start_date_dt).days
    
    #Seteamos el valor del simbolo
    pair = row['SYMBOL']
    
    # Verificamos si el delta es menor a 7 días e imprimimos la traza correspondiente
    if delta < 7:
        print(f"Traza: El delta es menor a 7 días. start_date: {start_date}, end_date: {end_date}, delta: {delta} días")
        
        ohlc_df = KrakenApiOHLC.get_ohlc_data_for_date_range(pair, '15', start_date, end_date)

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
        
    else:
        print(f"Traza: El delta es mayor o igual a 7 días. start_date: {start_date}, end_date: {end_date}, delta: {delta} días")
        
        ohlc_df = KrakenApiTrades.get_ohlc_data_for_date_range(pair, start_date, end_date, '15min')
        
        ohlc_spark_df = spark.createDataFrame(ohlc_df)
        
        ohlc_spark_df = (
            ohlc_spark_df
             # Transformaciones básicas
             .withColumn('origin', lit('ApiTrades'))
                    .withColumn('load_date', lit(current_date()))
                    .withColumn('symbol', lit(pair))
                    .withColumn('datetime', from_unixtime(col('timestamp')).cast('timestamp'))
                    .withColumn('year', col('datetime').substr(0, 4).cast('int'))
        )

    ohlc_df_total = ohlc_df_total.union(ohlc_spark_df)
ohlc_df_total.printSchema()
ohlc_df_total.show(5)
ohlc_df_total_casted = ohlc_df_total.select(
    col('TIMESTAMP').cast(esquema_bronze_df['TIMESTAMP'].dataType),
    col('OPEN').cast(esquema_bronze_df['OPEN'].dataType),
    col('HIGH').cast(esquema_bronze_df['HIGH'].dataType),
    col('LOW').cast(esquema_bronze_df['LOW'].dataType),
    col('CLOSE').cast(esquema_bronze_df['CLOSE'].dataType),
    col('VOLUME').cast(esquema_bronze_df['VOLUME'].dataType),
    col('TRADES').cast(esquema_bronze_df['TRADES'].dataType),
    col('ORIGIN').cast(esquema_bronze_df['ORIGIN'].dataType),
    col('LOAD_DATE').cast(esquema_bronze_df['LOAD_DATE'].dataType),
    col('SYMBOL').cast(esquema_bronze_df['SYMBOL'].dataType),
    col('DATETIME').cast(esquema_bronze_df['DATETIME'].dataType),
    col('YEAR').cast(esquema_bronze_df['YEAR'].dataType)
)

ohlc_df_total_casted.printSchema()
ohlc_df_total_casted.show(5)
#Persistencia de datos
(
    ohlc_df_total_casted
        .write
        .format('parquet')
        #.partitionBy('symbol','year')
        .partitionBy('LOAD_DATE')
        .mode('append')
        .save('s3://' + BUCKET + '/datalake/bronze/cryptos')
)
job.commit()