# Importación de las librerías requeridas para el análisis
import cryptoengineersdk as ce
import numpy as np
import pandas as pd
import ta
from datetime import datetime

def eval_model(model=None, StartDate="2024-04-30 23:45:00", EndDate="2024-09-01 00:00:00"):

    user_token = {
        "user": "hector",
        "token": "a9agHyfg5478GfufUfj98534fs4gHh89Ig7v6fG89kJy7U5f5FFhjU88"
    }

    StartDate = datetime.strptime(StartDate, "%Y-%m-%d %H:%M:%S") 
    EndDate = datetime.strptime(EndDate, "%Y-%m-%d %H:%M:%S")
    
    # Parámetros para la obtención de la moneda cuyos precios han de predecirse
    table_name = "silver_t_cryptos"
    symbol = "ETHUSD"
    FI = StartDate.year
    FF = EndDate.year
    
    # Carga de la información sobre la criptomoneda que ha de predecirse
    df_crypto = ce.reader(user_token, table_name, symbol, FI, FF)

    # Datasets disponibles de criptomonedas
    crypto_list = ["XBTUSD", "ETHUSD", "LINKUSD", "XDGUSD"]

    def load_crypto(df, crypto_file):
        
        # Definición del título de las columnas
        columns_names = [
            "Base_currency",
            "Type",
            "DateTime",
            "Date",
            "Time",
            "Frequency",
            "Month",
            "Day",
            f"{crypto_file}_Open",
            f"{crypto_file}_High",
            f"{crypto_file}_Low",
            f"{crypto_file}_Close", 
            f"{crypto_file}_Volume_USD", 
            f"{crypto_file}_Trades",
            "Audit_Time",
            "Symbol",
            "Year",
        ]
      
        # Añadir el nombre de las columnas al dataset
        df.columns = columns_names
        
        # Seleccionar únicamente las columnas con las que vamos a trabajar
        df = df[["DateTime", f"{crypto_file}_Close"]]
        
        # Eliminar primera fila, correspondiente al encabezado existente en la tabla por defecto
        df = df.drop(index=0).reset_index(drop=True)
        
        # Convertir en formato fecha la columna "DateTime"
        df["DateTime"] = pd.to_datetime(df["DateTime"])
        
        # Ordenar los registros en función del DateTime
        df = df.sort_values(by="DateTime")
        
        # Convertir columna de fecha en índice
        df = df.set_index("DateTime")
        
        # Castear los valores de las cotizaciones a tipo "float"
        df[f"{crypto_file}_Close"] = df[f"{crypto_file}_Close"].astype("float64")
    
        # Eliminar filas con índices duplicados
        df = df[~df.index.duplicated(keep="first")]
        
        return df
      
    # Carga del fichero de la criptomoneda cuyo valor ha de precederse
    crypto_file = crypto_list[1]
    df_crypto = load_crypto(df_crypto, crypto_file)

    # Función cuyos argumentos son un dataframe de Pandas y el número de cotizaciones sobre los que se calcula la media exponencial
    def calculate_trix(df, window=14):
        # Creación de una variable que recoge los nuevos valores calculadores mediante la técnica TRIX, aplicando la función correspondiente a las cotizaciones, según el intervalo definido.
        trix_indicator = ta.trend.TRIXIndicator(df[f"{crypto_file}_Close"], window=window)
        # Creación de una nueva columna que contiene el valor generado para cada período.
        df["TRIX"] = trix_indicator.trix()
        # Definición de una variable que recoge el cálculo de la media móvil simple aplicado a los valores TRIX, en un intervalo igual de 12 entradas.
        trix_signal_indicator = ta.trend.SMAIndicator(df["TRIX"], window=window)
        # Creación de una nueva columna que contiene el valor generado para cada período.
        df["TRIX_signal"] = trix_signal_indicator.sma_indicator()  
        
        return df

    # Definición de la función para la detección de patrones según ondas de Elliott
    def elliott_wave_detection(df):
        # Creación de una nueva columna vacía que contendrá los picos y valles de las ondas
        df["Wave_Pattern"] = np.nan
        # Castear la columna a tipo "string", para rellenar los registros con los valores "Peak" o "Trough"
        df["Wave_Pattern"] = df["Wave_Pattern"].astype(str)
        # Bucle que recorrerá las cotizaciones en busca de patrones de picos y valles
        for i in range(1, len(df)-1):
            # Si el precio en t es mayor que el precio en t-1 y es menor que el precio en t+1
            if df[f"{crypto_file}_Close"].iloc[i-1] < df[f"{crypto_file}_Close"].iloc[i] and df[f"{crypto_file}_Close"].iloc[i] > df[f"{crypto_file}_Close"].iloc[i+1]:
                # Alimentar la columna de patrones de ondas con el literal "Peak", pues el algoritmo habrá detectado un pico de cotización
                df.loc[df.index[i], "Wave_Pattern"] = 'Peak'
            # Si el precio en t es menor que el precio en t-1 y es mayor que el precio en t+1
            elif df[f"{crypto_file}_Close"].iloc[i-1] > df[f"{crypto_file}_Close"].iloc[i] and df[f"{crypto_file}_Close"].iloc[i] < df[f"{crypto_file}_Close"].iloc[i+1]:
                # Alimentar la columna de patrones de ondas con el literal "Trough", pues el algoritmo habrá detectado un valle de cotización
                df.loc[df.index[i], "Wave_Pattern"] = 'Trough'
        
        return df

    # Definición de una función para la estrategia de trading basada en TRIX y en ondas de Elliott
    def trading_strategy(df):
        # Partir fuera del mercado
        df["Signal"] = 0
        # Partir sin posición abierta, es decir, sin estar invertido.
        position_open = False  
        # Bucle que recorrerá las cotizaciones en busca del patrones de ondas de Elliott sobre los valores calculados en función de TRIX. 
        for i in range(1, len(df)):
            # Si el TRIX en t es menor que la media móvil del TRIX en t y si el TRIX en t -1 es menor que la media móvil del TRIX en t-1 y se confirma que existe un valle en t.
            if df["TRIX"].iloc[i-1] < df["TRIX_signal"].iloc[i-1] and df["TRIX"].iloc[i] > df["TRIX_signal"].iloc[i] and df["Wave_Pattern"].iloc[i] == 'Trough':
                # El algoritmo emite señal de compra
                df.loc[df.index[i], "Signal"] = 1
                # La posición para a estar abierta
                position_open = True
            # Si el TRIX en t-1 es mayor que la media móvil del TRIX en t-1 y si el TRIX en t es menor que la media móvil del TRIX en t y se confirma que existe un pico en t y existe posición abierta.
            elif df["TRIX"].iloc[i-1] > df["TRIX_signal"].iloc[i-1] and df["TRIX"].iloc[i] < df["TRIX_signal"].iloc[i] and df["Wave_Pattern"].iloc[i] == "Peak" and position_open:
                # El algoritmo emite seál de venta
                df.loc[df.index[i], "Signal"] = 0
                # La posición deja de estar abierta y pasamos a estar fuera del mercado.
                position_open = False
            # Si la posición está abierta
            elif position_open:
                # Continuar con la posición abierta.
                df.loc[df.index[i], "Signal"] = 1
        
        return df

    # Creación de una función en la que se simula una cartera con un capital inicial de 1.000 u.m.
    def simulate_trades(df, initial_capital=1000):
        # Definición de una variable que informa del capital disponible
        capital = initial_capital
        # Creación de una variable que informa de la posición invertida
        position = 0
        # Creación de una variable en la que se almacenará el tipo de orden anterior ("Buy", "Sell", "None")
        last_order = None
        # Creación de una lista vacía en la que se almacenarán todos los registros en frecuencias de 15 minutos, que informarán de las señales y demás información
        results = []
    
        # Bucle que recorrerá cada entrada/cotización, en frecuencias de 15 minutos.
        for i in range(1, len(df)):
            # Creación de una variable que se alimentará con el último precio cotizado de la criptomoneda
            current_price = df[f"{crypto_file}_Close"].iloc[i]
            # Creación de una variable que se alimentará con la último señal que emita el algoritmo
            signal = df["Signal"].iloc[i]
    
            # Si el algoritmo emite señal de venta y la última orden fue distinta de compra y existe capital en la cartera, se ejecuta una compra.
            if signal == 1 and last_order != "Buy" and capital > 0:
                # Se invierte todo el capital
                invest_amount = capital
                # La posición invertida es igual al capital disponible dividido entre el precio
                position += invest_amount / current_price
                # El capital disponible pasa a ser nulo
                capital = 0
                # Añadir el registro al dataframe de salida.
                results.append({
                    "DATETIME": df.index[i],
                    "CLOSE": current_price,
                    "SIGNAL": signal
                })
                # La última orden viva es una compra
                last_order = "Buy"
    
            # Si el algoritmo emite señal de venta y la última orden fue distinta de venta y existe capital en la cartera, se ejecuta una venta.
            elif signal == 0 and last_order != "Sell" and position > 0: 
                # Se vende todo el capital invertido al precio de mercado
                amount_sold = position * current_price
                # El capital disponible ahora es el importe vendido
                capital += amount_sold
                # Añadir el registro al dataframe de salida.
                results.append({
                    "DATETIME": df.index[i],
                    "CLOSE": current_price,
                    "SIGNAL": signal
                })
                # El capital invertido pasa a ser nulo.
                position = 0
                # La última orden viva es una venta.
                last_order = 'Sell'
            # Si el algoritmo no emite orden de compra o de venta, se mantiene fuera del mercado.
            else:
                # Añadir el registro al dataframe de salida.
                results.append({
                    "DATETIME": df.index[i],
                    "CLOSE": current_price,
                    "SIGNAL": signal
                })

        return pd.DataFrame(results)

    # Aplicar funciones
    df_crypto = calculate_trix(df_crypto)
    df_crypto = elliott_wave_detection(df_crypto)
    df_crypto = trading_strategy(df_crypto)
    df_results = simulate_trades(df_crypto)
        
    return df_results