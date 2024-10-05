import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
import statsmodels.tsa.stattools as sts
import cryptoengineersdk as ce



def eval_model(modelo_arimax, fec_ini, fec_fin):
    user_token = {

    "user": "carlos",

    "token": "iasdi88fHFy54f3F875f98h9Mmnjojm32jh12xS57d32123n67888Mjf"

    }

    table_name = "silver_t_commodities" # Es obligatorio

    symbol = 'ALL_SYMBOLS' # Es opcional, si no lo indicas leerá todos los symbols de la tabla.

    from_year = 2024 # Es opcional, si no lo indicas leerá desde la fecha más antigua

    to_year = 2024 # Es opcional, si no lo indicas leerá hasta la fecha más reciente


    df_commodities24 = ce.reader(user_token, table_name, symbol, from_year, to_year)

    # Eliminar directamente en el DataFrame original
    df_commodities24 = df_commodities24[df_commodities24["FREQUENCY"] != "15min"]

    table_name = "silver_t_forex" # Es obligatorio

    symbol = 'ALL_SYMBOLS' # Es opcional, si no lo indicas leerá todos los symbols de la tabla.

    from_year = 2024 # Es opcional, si no lo indicas leerá desde la fecha más antigua

    to_year = 2024 # Es opcional, si no lo indicas leerá hasta la fecha más reciente


    df_forex24 = ce.reader(user_token, table_name, symbol, from_year, to_year)

    table_name = "silver_t_indices" # Es obligatorio

    symbol = 'ALL_SYMBOLS' # Es opcional, si no lo indicas leerá todos los symbols de la tabla.

    from_year = 2024 # Es opcional, si no lo indicas leerá desde la fecha más antigua

    to_year = 2024 # Es opcional, si no lo indicas leerá hasta la fecha más reciente

    df_indices24 = ce.reader(user_token, table_name, symbol, from_year, to_year)

    table_name = "silver_t_cryptos" # Es obligatorio

    symbol = 'ALL_SYMBOLS' # Es opcional, si no lo indicas leerá todos los symbols de la tabla.

    from_year = 2024 # Es opcional, si no lo indicas leerá desde la fecha más antigua

    to_year = 2024 # Es opcional, si no lo indicas leerá hasta la fecha más reciente

    df_cryptos24 = ce.reader(user_token, table_name, symbol, from_year, to_year)
    
    # Definir la lista de DataFrames
    dataframes = [df_indices24, df_forex24, df_cryptos24, df_commodities24]

    # Definir las columnas deseadas 
    columnas_seleccionadas = ["BASE_CURRENCY", "TYPE", "DATE", "DATETIME", "CLOSE", "SYMBOL"]

    # Crear una lista vacía para almacenar los resultados filtrados
    df_filtrados = []

    # Bucle for para iterar sobre los DataFrames
    for df in dataframes:
        # Filtrar las columnas seleccionadas
        df_filtrado = df[columnas_seleccionadas]

        # Asegurarse de que la columna DATETIME esté en formato datetime
        df_filtrado['DATETIME'] = pd.to_datetime(df_filtrado['DATETIME'])

        # Ordenar los datos por DATETIME para asegurarnos de tener el último registro al final
        df_filtrado = df_filtrado.sort_values(by='DATETIME')

        # Filtrar el último registro de cada día para cada SYMBOL
        df_ultimo_symbol = df_filtrado.groupby(['SYMBOL', 'DATE']).tail(1)

        # Agregar el resultado filtrado a la lista
        df_filtrados.append(df_ultimo_symbol)

    # Concatenar los resultados de los DataFrames en uno solo
    df_final24 = pd.concat(df_filtrados)

    # 1. Filtrar el DataFrame para obtener los registros del símbolo XDGUSD
    df_BTC_symbol24 = df_final24[df_final24['SYMBOL'] == 'XBTUSD'].copy()

    # 2. Renombrar la columna 'CLOSE' a 'label' para usarla más adelante
    df_BTC_symbol24 = df_BTC_symbol24[['DATE', 'CLOSE']].rename(columns={'CLOSE': 'label'})

    # 3. Realizar un merge con el df_final, usando la columna DATE para emparejar los valores
    df_BTC24 = pd.merge(df_final24, df_BTC_symbol24, on='DATE', how='left')

    # 4. Filtrar de nuevo si solo quieres quedarte con los registros de DOGE
    df_BTC24 = df_BTC24[df_BTC24['SYMBOL'] != 'XBTUSD'].reset_index(drop=True)

    # 1. Usar pivot_table para transformar el DataFrame
    df_pivot_BTC24 = df_BTC24.pivot_table(index='DATE', columns='SYMBOL', values='CLOSE')

    # 2. Renombrar las columnas para que sean más claras
    df_pivot_BTC24.columns = [f'{col}_CLOSE' for col in df_pivot_BTC24.columns]

    # 3. Añadir la columna 'label' al DataFrame df_doge
    df_labels24 = df_BTC24[['DATE', 'label']].drop_duplicates()

    # 4. Hacer un merge para combinar los datos pivotados con la columna 'label'
    df_pivot_BTC24 = df_pivot_BTC24.reset_index()
    df_final_BTC24 = pd.merge(df_pivot_BTC24, df_labels24, on='DATE', how='left')

    # 5. Rellenar valores faltantes usando backward fill
    df_final_BTC24 = df_final_BTC24.fillna(method='bfill')

    df_final_BTC24["DATE"] = pd.to_datetime(df_final_BTC24["DATE"])  # Convertir a datetime si no se ha hecho
    df_final_BTC24.set_index("DATE", inplace=True)  # Asegurar que DATE es el índice

    # Filtrar registros hasta el 1 de SEPT de 2024
    df_filtrado24 = df_final_BTC24.loc[:'2024-09-01']
    
    # Convertir las fechas a formato datetime
    fec_ini = pd.to_datetime(fec_ini)
    fec_fin = pd.to_datetime(fec_fin)

    # Filtrar los datos por el rango de fechas especificado (usando el índice)
    df_filtrado24 = df_filtrado24.loc[fec_ini:fec_fin]

    # Extraer los valores exógenos para el rango de fechas
    exog_values = df_filtrado24.loc[:, ["SP500_CLOSE", "GCUSD_CLOSE", "Nasdaq_CLOSE", "USDEUR_CLOSE"]]

    # Asegurar de que las dimensiones son correctas
    print("Dimensiones de exog_values:", exog_values.shape)

    # Realizar la predicción
    predicciones = modelo_arimax.predict(
        start=len(df_filtrado24)-len(exog_values),  # Ajustar el índice de inicio
        end=len(df_filtrado24)-1,  # Fin debe coincidir con el último valor
        exog=exog_values
    )

    # Calcular la señal: 1 si el valor del día siguiente es mayor que el anterior, 0 si es menor
    signal = np.where(np.diff(predicciones) > 0, 1, 0)

    # Ajustar la longitud de las variables para que coincida con 'signal' (una observación menos por el diff)
    DATE = df_filtrado24.index[1:]  # Usar el índice como DATE
    CLOSE = df_filtrado24['label'].iloc[1:].reset_index(drop=True)  # Extraer el label de la columna

    # Crear un DataFrame con los resultados
    df_result = pd.DataFrame({
        'DATETIME': DATE,
        'CLOSE': CLOSE,
        'SIGNAL': signal
    }).reset_index(drop=True)  # Restablecer el índice

    return df_result

