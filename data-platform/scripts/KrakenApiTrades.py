import requests
import pandas as pd
import datetime
import time

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

# Define the function to get trade data from Kraken with pagination
def get_trade_data_with_pagination(pair, start_time, end_time, max_retries=5):
    """
    Obtiene datos de transacciones de Kraken para un par específico, utilizando paginación para manejar grandes volúmenes de datos.
    
    Args:
        pair (str): El par de divisas (ej. 'XBTUSDC').
        start_time (datetime.datetime): Objeto datetime representando el inicio del rango de tiempo.
        end_time (datetime.datetime): Objeto datetime representando el final del rango de tiempo.
        max_retries (int, opcional): Número máximo de reintentos si se encuentra el mismo último tiempo de transacción. Por defecto es 5.
    
    Returns:
        pandas.DataFrame: DataFrame que contiene columnas de price, volume, time, buy_sell, market_limit, miscellaneous y trade_id.
    """
   
    trade_data = []
    since = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())
    retry_count = 0

    print(f"Starting data retrieval from {start_time} to {end_time}")

    while since < end_timestamp:
        url = f'https://api.kraken.com/0/public/Trades?pair={pair}&since={since}'
        response = requests.get(url)
        data = response.json()
        
        if data['error']:
            print(f"Error fetching data: {data['error']}")
            time.sleep(15)
            continue
        new_trades = data['result'][list(data['result'].keys())[0]]
        last_trade_time = int(new_trades[-1][2])
        
        print(f"Retrieved {len(new_trades)} new trades. Last trade time: {datetime.datetime.utcfromtimestamp(last_trade_time)}")
        
        if last_trade_time == since:
            retry_count += 1
            if retry_count >= max_retries:
                print("Max retries reached. Exiting.")
                trade_data.extend(new_trades)
                since = since + 1  # Move to the next second to avoid infinite loop
            print("Same last trade time encountered. Retrying...")
            time.sleep(1)  # Wait for a second before retrying
        else:
            trade_data.extend(new_trades)
            since = last_trade_time
            retry_count = 0
        
        time.sleep(1)  # Respect rate limits by sleeping between requests
    
    df = pd.DataFrame(trade_data, columns=[
        'price', 'volume', 'time', 'buy_sell', 'market_limit', 'miscellaneous', 'trade_id'
    ])
    
    # Convert price and volume to numeric types
    df['price'] = pd.to_numeric(df['price'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    # Convert timestamp to datetime and set as index for resampling
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    print(f"Data retrieval complete. Total trades retrieved: {len(trade_data)}")
    
    return df

# Function to calculate OHLC from trade data
def calculate_ohlc(trade_df, interval='15min'):
    """
    Calcula los datos OHLC (Open, High, Low, Close) a partir de los datos de transacciones utilizando un intervalo específico.

    Args:
        trade_df (pandas.DataFrame): DataFrame que contiene datos de transacciones.
        interval (str, opcional): Intervalo de tiempo para calcular los datos OHLC. Por defecto es '15min'.

    Returns:
        pandas.DataFrame: DataFrame que contiene columnas de timestamp, open, high, low, close, volume y trades.
    """
    
    print(f"Calculating OHLC data with interval: {interval}")
    
    # Resample data using the 'time' column as the index
    ohlc_df = trade_df.resample(interval, on='time').agg({
        'price': ['first', 'max', 'min', 'last'],
        'volume': 'sum',
        'time': 'count'
    }).dropna()
    
    # Flatten column names
    ohlc_df.columns = ['open', 'high', 'low', 'close', 'volume', 'trades']
    
    # Reset index to make 'time' a column again and keep Unix timestamp
    ohlc_df.reset_index(inplace=True)
    ohlc_df['timestamp'] = ohlc_df['time'].astype(int) // 10**9  # Convert to Unix timestamp

    # Drop the datetime column since it's not required in the final output
    ohlc_df.drop(columns=['time'], inplace=True)
    
    print("OHLC calculation complete.")
    
    return ohlc_df

# Function to get OHLC data for a date range
def get_ohlc_data_for_date_range(pair, start_date, end_date, interval='15min'):
    """
    Obtiene datos OHLC (Open, High, Low, Close) para un par específico en un rango de fechas dado.

    Args:
        pair (str): El par de divisas (ej. 'XBTUSDC').
        start_date (str): Fecha de inicio en formato "dd-mm-yyyy".
        end_date (str): Fecha de fin en formato "dd-mm-yyyy".
        interval (str, opcional): Intervalo de tiempo para calcular los datos OHLC. Por defecto es '15min'.

    Returns:
        pandas.DataFrame: DataFrame que contiene columnas de timestamp, open, high, low, close, volume y trades.
    """
    
    # Convert start_date and end_date from string to datetime objects
    start_date = convert_to_datetime(start_date)
    end_date = convert_to_datetime(end_date)
    
    print(f"Fetching trade data for {pair} from {start_date} to {end_date}")
    trade_df = get_trade_data_with_pagination(pair, start_date, end_date)
    ohlc_df = calculate_ohlc(trade_df, interval)
    ohlc_df = ohlc_df[ohlc_df['timestamp'] < int(end_date.timestamp())]
    ohlc_df = ohlc_df[['timestamp','open', 'high', 'low', 'close', 'volume', 'trades']]
    print(f"OHLC data for the range from {start_date} to {end_date} is ready.")
    return ohlc_df


# Define the pair, start date, and end date
#pair = 'XBTUSDC'
#start_date = "01-08-2024"  # As string in dd-mm-yyyy format
#end_date = "22-09-2024"    # As string in dd-mm-yyyy format
#
## Get the OHLC data for the specified date range
#ohlc_df = get_ohlc_data_for_date_range(pair, start_date, end_date, '15min')
#print(ohlc_df.head())
#
#ohlc_df.to_csv("BTC_15.csv", header=True)
