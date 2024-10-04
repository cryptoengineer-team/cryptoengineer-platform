# -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 11:12:33 2024

@author: Luis
"""
import pandas as pd
import datetime
import requests

# Function to convert date string to a datetime object
def convert_to_datetime(date_str):
    """
    Convierte una cadena de fecha a un objeto datetime.

    Args:
        date_str (str): Fecha en formato "dd-mm-yyyy".

    Returns:
        datetime.datetime: Objeto datetime correspondiente a la fecha dada.
    """
    
    return datetime.datetime.strptime(date_str, "%d-%m-%Y")

# Define the function to get OHLC data from Kraken
def get_ohlc_data_for_date_range(pair, interval=15, start_date=None, end_date=None):
    """
    Obtiene datos OHLC (Open, High, Low, Close) de Kraken para un par específico en un rango de fechas dado.

    Args:
        pair (str): El par de divisas (ej. 'XBTUSDC').
        interval (int, opcional): Intervalo de tiempo en minutos para los datos OHLC. Por defecto es 15 minutos.
        start_date (str, opcional): Fecha de inicio en formato "dd-mm-yyyy".
        end_date (str, opcional): Fecha de fin en formato "dd-mm-yyyy".

    Returns:
        pandas.DataFrame: DataFrame que contiene columnas de timestamp, open, high, low, close, volume y trades.
    """
    
    start_date = convert_to_datetime(start_date)
    end_date = convert_to_datetime(end_date)
    
    since = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    url = f'https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}&since={since}'
    
    response = requests.get(url)
    data = response.json()
    
    if data['error']:
        raise Exception(f"Error fetching data: {data['error']}")
    
    ohlc_data = data['result'][list(data['result'].keys())[0]]
    
    df = pd.DataFrame(ohlc_data, columns=[
        'time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
    ])
    
    # Filter data within the end date
    df = df[df['time'] <= end_timestamp]
    
    # Convert timestamp to datetime
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Rename columns to match the desired structure
    df.rename(columns={
        'time': 'timestamp',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'count': 'trades'
    }, inplace=True)
    
    # Convert the timestamp back to Unix timestamp
    df['timestamp'] = df['timestamp'].astype(int) // 10**9
    
    # Select the required columns
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'trades']]
    
    return df


# Define the pair, interval, and date range
#pair = 'XBTUSDC'
#interval = 15  # 15 minute interval
#start_date = "01-01-2024"  # Start date as string in dd-mm-yyyy format
#end_date = "10-08-2024"    # End date as string in dd-mm-yyyy format

# Get the OHLC data
#api_df = get_ohlc_data_for_date_range(pair, interval, start_date, end_date)
#print(api_df.head())
