import os
import pandas as pd
import requests
from calendar import monthrange
from datetime import datetime, timedelta

# Helper functions
def return_url_base(source: str = "CB",
                    metric: str = 'rates',
                    type: str = 'historical',
                    freq: str = None):
    URL_BASE=None
    if source == 'CB':
        # Set the base URL
        URL_BASE='https://api.currencybeacon.com/v1'
        if type == 'historical':
            URL_BASE=URL_BASE+'/timeseries'
        else:
            URL_BASE=URL_BASE+'/latest' 
    elif source == 'FMP':
        # Set the base URL
        URL_BASE='https://financialmodelingprep.com/api/v3'
        if type == 'historical':
            URL_BASE=URL_BASE+'/historical-price-full'
        elif type == 'frequency' and freq:
            URL_BASE=URL_BASE+f'/historical-chart/{freq}'
        else:
            URL_BASE=URL_BASE+'/quote' 
        
    #URL_BASE='https://api.currencybeacon.com/v1/timeseries'
    
    return URL_BASE

def get_url(url_base: str,
            base: str,
            start_date: str,
            end_date: str,
            symbols: str = "EUR,CHF,JPY,CAD,GBP",
            source: str = "CB",
            api_key: str = None,
    ):
    # Get the API key from the environment variable
    api_key= api_key if api_key is not None else os.environ['CURRENCYBEACON_API']
    # Set the API key
    # Generate the complete URL
    if source == 'CB':
        api_key='?api_key='+api_key
        url=url_base+api_key+'&base='+base+'&start_date='+start_date+'&end_date='+end_date+'&symbols='+symbols
    elif source == 'FMP':
        api_key='?apikey='+api_key
        url=url_base+'/'+symbols+api_key
    return url

def to_df(json_response: dict, source: str = "CB"):
    # Load the json response into a pandas dataframe
    if source == "CB":
        # Load the json response into a pandas dataframe
        response = json_response['response']
    elif source == "FMP":
        response = json_response['historical']
    # Convert the json response to a pandas dataframe        
    #df = pd.DataFrame.from_dict(json_response, orient="index")        
    df = pd.DataFrame.from_records(response)
    
    return df
##### END HELPER FUNCTIONS

#####################################
# Function to read historical rates
#####################################
def ingest_historical_rates(base: str,
                        start_date: str,
                        end_date: str,
                        symbols: str = "EUR,CHF,JPY,CAD,GBP",
                        api_key: str = None,
                        source: str = "CB",
                        ):
    
    # Get the URL base
    URL_BASE=return_url_base(source, 'rates', 'historical')
    print(URL_BASE)
    # Set the API key
    # Generate the complete URL
    url= get_url(URL_BASE,base,start_date,end_date,symbols,source,api_key)
    print(url)
    # Get the response from the URL
    data = requests.get(url)
    
    # IF status 200 return data
    if data.status_code == 200:
        print('Lectura API correcta')
        return data.json()
    else:
        return None

def load_historical_rates(base: str,
                        start_date: str,
                        end_date: str,
                        symbols: str = "EUR,CHF,JPY,CAD,GBP",
                        api_key: str = None,
                        source: str = "CB",
                        ):
    # Read the API to get historical data
    response=ingest_historical_rates(base, start_date, end_date, symbols, api_key,  source)
    # Converto to df
    df = to_df(response, source)
    # Filter by date and create the new columns symbol, source and freq
    df = (
            df
            [(df['date']>=start_date) & (df['date']<=end_date)]
            .assign(symbol=symbols)
            .assign(source='FMP')
            .assign(freq='1day')
        )

    return df

#####################################
# Function to read latset rates
#####################################

def ingest_latest_rates(base: str,
                        symbols: str = "EUR,CHF,JPY,CAD,GBP",
                        api_key: str = None,
                        source: str = "CB",                        
                        ):
                        
    # Get the URL base
    URL_BASE=return_url_base(source, 'rates', 'latest')
    # Set the API key
                        
#    URL_BASE='https://api.currencybeacon.com/v1/latest'
    url= get_url(URL_BASE,base,None,None,symbols,source,api_key)

    # Generate the URL
    print(url)
    # Get the response from the URL
    data = requests.get(url)
    
    # IF status 200 return data
    if data.status_code == 200:
        if source == 'CB':
            print('Lectura API correcta')
            return data.json()['response']
        elif source == 'FMP':
            print('Lectura API correcta')
            return data.json()
        else:
            return None
    else:
        return None
    
def load_latest_rates(base: str,
                        symbols: str = "EUR,CHF,JPY,CAD,GBP",
                        api_key: str = None,
                        source: str = "CB",
                        ):
    # Read the API to get latest data
    response=ingest_latest_rates(base, symbols, api_key, source)
    # Converto to df
    #df = to_df(response)
    print("Response ", response)

    return response


#####################################
# Function to read historical rates by frequency
#####################################

def ingest_historical_freq_rates(base: str,
                        year: int,
                        month: int,
                        freq: str,
                        symbol: str = "USDEUR",
                        api_key: str = None,
                        source: str = "FMP",
                        ):
    
    # Get the URL base
    URL_BASE=return_url_base(source, 'rates', 'frequency', freq)
    #print(URL_BASE)
    # Set the API key
    api_key= api_key if api_key is not None else os.environ['FMP_API_KEY']
    api_key='?apikey='+api_key


    if month:
        #print("Reading month")
        start_date=f'{year}-{month:02d}-01'
        end_date=f'{year}-{month:02d}-{monthrange(year, month)[1]:02d}'
        #print("Desde ",start_date," hasta ",end_date)
        url=URL_BASE+'/'+symbol+api_key+'&from='+start_date+'&to='+end_date
        #print(url)
        data = requests.get(url)
        
        if data.status_code == 200:
            #print('Lectura API correcta')
            listado=data.json()
            #print(data.content)
            #print("Listado: \n", listado)
            #print("Leidos ",len(listado))
        else:
            listado=None

    else:
        listado=[]
        for month in range(1,13):
            start_date=f'{year}-{month:02d}-01'
            end_date=f'{year}-{month:02d}-{monthrange(year, month)[1]:02d}'
            url=URL_BASE+'/'+symbol+api_key+'&from='+start_date+'&to='+end_date
            #print(url)
            data = requests.get(url)
            if data.status_code == 200:
                #print('Lectura API correcta')
                listado+=data.json()
            else:
                listado+=None
                break
            
    #print("Returning ",len(listado))
    return listado  

def load_historical_freq_rates(base: str,
                        start_date: str,
                        end_date: str,
                        freq: str,
                        symbol: str = "USDEUR",
                        api_key: str = None,
                        source: str = "FMP",
                        ):

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    # initialize the list of rates
    listado=[]
    while start_date <= end_date:
            # Extract the year and month to read
            year=start_date.year
            month=start_date.month
            print("Year: ", year," Month:", month)
            # Send the requests for the year-month
            listado+=ingest_historical_freq_rates(base=base,
                            year=year,
                            month=month,
                            freq=freq,
                            symbol = symbol,
                            api_key = api_key,
                            source = source,
                            )
            # Calculate the start date for the next month
            days = monthrange(start_date.year, start_date.month + 1 if start_date.month < 12 else 1)[1]
            start_date = start_date + timedelta(days=days)
            print("Leidos ",len(listado))

    print (end_date.strftime("%Y-%m"))

    # Read the last month
    if start_date.month <= end_date.month: 
        year=start_date.year
        month=start_date.month
        print("Year: ", year," Month:", month)
        listado+=ingest_historical_freq_rates(base=base,
                                            year=year,
                                            month=month,
                                            freq=freq,
                                            symbol = symbol,
                                            api_key = api_key,
                                            source = source,
                )
    print("Leidos ",len(listado))
    print("Creating the dataframe")
    data = pd.DataFrame.from_records(listado)
    data['symbol']=symbol
    data['source']=source
    data['freq']=freq
    
    return data

##
## Load batch data
##
def ingest_batch_freq_rates(base: str,
                        start_date: str,
                        end_date: str,
                        freq: str,
                        symbol: str = "USDEUR",
                        api_key: str = None,
                        source: str = "FMP",
                        ):
    
    # Get the URL base
    URL_BASE=return_url_base(source, 'rates', 'frequency', freq)
    #print(URL_BASE)
    # Set the API key
    api_key= api_key if api_key is not None else os.environ['FMP_API_KEY']
    api_key='?apikey='+api_key

    #print("Reading batch")
    #start_date=f'{year}-{month:02d}-01'
    #end_date=f'{year}-{month:02d}-{monthrange(year, month)[1]:02d}'
    #print("Desde ",start_date," hasta ",end_date)
    url=URL_BASE+'/'+symbol+api_key+'&from='+start_date+'&to='+end_date
    #print(url)
    data = requests.get(url)
        
    if data.status_code == 200:
        #print('Lectura API correcta')
        listado=data.json()
        #print(data.content)
        #print("Listado: \n", listado)
        #print("Leidos ",len(listado))
    else:
        listado=None
            
    #print("Returning ",len(listado))
    return listado  

def load_batch_freq_rates(base: str,
                        start_date: str,
                        end_date: str,
                        freq: str,
                        symbol: str = "USDEUR",
                        api_key: str = None,
                        source: str = "FMP",
                        ):

    #start_date = datetime.strptime(start_date, "%Y-%m-%d")
    #end_date = datetime.strptime(end_date, "%Y-%m-%d")
    # initialize the list of rates
    listado=[]
    if start_date <= end_date:
            # Send the requests for the year-month
        listado=ingest_batch_freq_rates(base=base,
                            start_date=start_date,
                            end_date=end_date,
                            freq=freq,
                            symbol = symbol,
                            api_key = api_key,
                            source = source,
                            )

    print("Leidos ",len(listado))
    print("Creating the dataframe")
    data = pd.DataFrame.from_records(listado)
    data['symbol']=symbol
    data['source']=source
    data['freq']=freq
    
    return data

##
##
##
def ingest_latest_rates_TE(base: str,
                        symbols: str = "EUR,CHF,JPY,CAD,GBP",
                        api_key: str = None,
                        source: str = "CB",                        
                        ):
                        
    # Get the URL base
    URL_BASE=return_url_base(source, 'rates', 'latest')
    # Set the API key
                        
    url = "https://tradingeconomics.com/currencies"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    response = requests.get(url, headers=headers)
    
    api_key= api_key if api_key is not None else os.environ['CURRENCYBEACON_API']
    api_key='?api_key='+ api_key
    # Generate the URL
    url=URL_BASE+api_key+'&base='+base+'&symbols='+symbols
    print(url)
    # Get the response from the URL
    data = requests.get(url)
    
    # IF status 200 return data
    if data.status_code == 200:
        return data.json()['response']
    else:
        return None
