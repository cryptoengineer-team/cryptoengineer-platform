import pandas as pd
import numpy as np
import cryptoengineersdk as ce  

# Se define la función eval_model con parámetros de fechas de inicio, fin y un modelo nulo
def eval_model(model, fec_ini, fec_fin):

    # Se define el user_token con las credenciales del usuario
    user_token = {
        "user": "eugenio",
        "token": "2J32Hhfwh2h2hk2Ik2hi2i75adsf6gGaASDFA98769h239as9vSD99oj"
    }
    
    # Se convierten las fechas de inicio y fin a formato datetime
    fec_ini = pd.to_datetime(fec_ini)
    fec_fin = pd.to_datetime(fec_fin)

    # Se leen los datos de LINKUSD utilizando la SDK de cryptoengineersdk
    table_name = "silver_t_cryptos"  # Nombre de la tabla
    crypto_file = "LINKUSD"  # Se define el símbolo específico

    # Se obtienen los datos de LINKUSD desde la tabla correspondiente
    crypto_df = ce.reader(user_token, table_name, symbol=crypto_file, from_year=fec_ini.year, to_year=fec_fin.year)

    # Se convierten los resultados obtenidos en un DataFrame de pandas
    crypto_df = pd.DataFrame(crypto_df)

    # Se ajustan los nombres de las columnas basados en los datos cargados
    column_names = [
        "BASE_CURRENCY", "TYPE", "DATETIME", "DATE", "TIME", "FREQUENCY", "MONTH", "DAY",
        f"{crypto_file}_Open", f"{crypto_file}_High", f"{crypto_file}_Low", f"{crypto_file}_Close",
        f"{crypto_file}_Volume", f"{crypto_file}_Trades", "AUDIT_TIME", "SYMBOL", "YEAR"
    ]
    
    # Se renombran las columnas del DataFrame con los nuevos nombres establecidos
    crypto_df.columns = column_names

    # Se transforman las columnas de año, mes y día en enteros para crear la fecha completa
    crypto_df['YEAR'] = crypto_df['YEAR'].astype(int)
    crypto_df['MONTH'] = crypto_df['MONTH'].astype(int)
    crypto_df['DAY'] = crypto_df['DAY'].astype(int)

    # Se crea la columna de fecha y hora combinando las columnas de año, mes, día y hora
    crypto_df['Full_Date'] = pd.to_datetime(crypto_df[['YEAR', 'MONTH', 'DAY']].astype(str).agg('-'.join, axis=1) + ' ' + crypto_df['TIME'])
    
    # Se establece el índice en la columna de fecha completa para resamplear los datos
    crypto_df.set_index('Full_Date', inplace=True)

    # Se resamplean los datos a intervalos de 15 minutos y se eliminan las filas con valores nulos
    crypto_df = crypto_df.resample('15T').last().dropna()

    # Se aplica el filtro para seleccionar los datos que caen dentro del rango de fechas deseado
    crypto_df = crypto_df[(crypto_df.index >= fec_ini) & (crypto_df.index <= fec_fin)]

    # Se añaden medias móviles y RSI para tomar decisiones de trading
    short_ma_window = 50  # Se establece la ventana para la media móvil corta
    long_ma_window = 200  # Se establece la ventana para la media móvil larga

    # Se calculan las medias móviles a corto y largo plazo
    crypto_df['Short_MA'] = crypto_df[f'{crypto_file}_Close'].rolling(window=short_ma_window).mean()
    crypto_df['Long_MA'] = crypto_df[f'{crypto_file}_Close'].rolling(window=long_ma_window).mean()

    # Se definen los niveles de RSI para generar señales de compra/venta
    rsi_window = 2  # Se establece la ventana del RSI
    rsi_buy_level = 30  # Nivel de RSI para compra
    rsi_sell_level = 80  # Nivel de RSI para venta

    # Se define la función para calcular el RSI
    def calculate_rsi(data, window=rsi_window):
        # Se calculan los cambios en los precios
        delta = data.diff(1)
        # Se calculan las ganancias y pérdidas
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        # Se calcula la relación entre ganancias y pérdidas (RS)
        rs = gain / loss
        # Se calcula el RSI basado en RS
        rsi = 100 - (100 / (1 + rs))
        return rsi

    # Se calcula el RSI sobre los precios de cierre y se manejan los NaN iniciales
    crypto_df['RSI'] = calculate_rsi(crypto_df[f'{crypto_file}_Close']).fillna(50)

    # Se generan las señales de compra/venta basadas en el RSI y las medias móviles
    crypto_df['Signal'] = 0
    crypto_df['Signal'] = np.where(
        (crypto_df['RSI'] < rsi_buy_level) & (crypto_df['Short_MA'] > crypto_df['Long_MA']), 1,
        np.where((crypto_df['RSI'] > rsi_sell_level) & (crypto_df['Short_MA'] < crypto_df['Long_MA']), -1, 0)
    )

    # Se registran las señales de las posiciones
    crypto_df['Position'] = crypto_df['Signal'].diff()

    # Se crea un DataFrame con las señales y columnas necesarias
    signals_df = crypto_df[['DATETIME', f'{crypto_file}_Close', 'Signal']].copy()
    signals_df.rename(columns={'DATETIME': 'DATETIME', f'{crypto_file}_Close': 'CLOSE', 'Signal': 'SIGNAL'}, inplace=True)

    # Se devuelve la señal, el datetime, el symbol, el close y el signal para integrar con la aplicación
    return signals_df

