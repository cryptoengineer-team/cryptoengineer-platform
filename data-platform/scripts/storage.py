import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
import json

from io import BytesIO
from datetime import datetime

# Set up S3 client
s3_client = boto3.client('s3')

def upload_df_s3_parquet_by_year(df, bucket_name, folder_prefix, date_column):
    """Upload a DataFrame to S3 in Parquet format partitioned by year from the date column."""
    
    # Ensure the date column is in datetime format
    df[date_column] = pd.to_datetime(df[date_column])

    # Extract the year from the date column
    df['year'] = df[date_column].dt.year

    # Group by year and save each group as a separate Parquet file
    for year, group in df.groupby('year'):
        # Convert DataFrame group to PyArrow Table
        table = pa.Table.from_pandas(group.drop(columns=['year']))
        
        # Create a buffer to hold the Parquet data
        buffer = BytesIO()
        
        # Write the table to the buffer in Parquet format
        pq.write_table(table, buffer, compression='snappy')
        
        # Create the S3 key for the Parquet file
        s3_key = f"{folder_prefix}/year={year}/data.parquet"
        
        # Upload the Parquet file to S3
        buffer.seek(0)
        s3_client.upload_fileobj(buffer, bucket_name, s3_key)
        
        print(f"Uploaded data for year {year} to {s3_key}")

def upload_df_s3_parquet(df, bucket_name, folder_prefix):
    """Upload a DataFrame to S3 in Parquet format partitioned by year from the date column."""
    
    s3_url = f's3://{bucket_name}/{folder_prefix}/data.parquet'
    print("Records to save: ", len(df))
    df.to_parquet(s3_url, compression='snappy')    
    print("Data frame saved")
    
def upload_json_s3(json_data, bucket_name, folder_prefix, filename):
    """Upload a DataFrame to S3 in Parquet format partitioned by year from the date column."""
    # Create a buffer to hold the Parquet data
    buffer = BytesIO()
        
    buffer.write(json.dumps(json_data).encode('utf-8'))
    buffer.seek(0)        
    # Create the S3 key for the Parquet file
    s3_key = f"{folder_prefix}/{filename}"
        
    # Upload the Parquet file to S3
    #buffer.seek(0)
    s3_client.upload_fileobj(buffer, bucket_name, s3_key)
        
    print(f"Uploaded data to {s3_key}")

