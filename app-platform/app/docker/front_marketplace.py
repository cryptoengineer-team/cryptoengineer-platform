import streamlit as st
import boto3
import json
from botocore.exceptions import NoCredentialsError, ClientError
import requests
import io
import pandas as pd
import numpy as np
#session = boto3.Session(profile_name='default')

# Configuración de AWS
#aws_access_key_id = st.secrets["default"]["aws_access_key_id"]
#aws_secret_access_key = st.secrets["default"]["aws_secret_access_key"]
#aws_session_token = st.secrets["default"]["aws_session_token"]

s3_client = boto3.client('s3')

lambda_client = boto3.client('lambda')

bucket_name = 'cryptoengineer'
URL_API_TOKEN = "https://o2grj23ube.execute-api.us-east-1.amazonaws.com/dev"
account_id = "212430227630"
lambda_name = "job_model_eval"


# Función para autenticar usuario
def user_auth(usuario, password):
    response = requests.get(f"{URL_API_TOKEN}/token/{usuario}/{password}")
    if response.content.decode('utf-8').strip("\"") == "Granted access":
        return True
    else:
        return False
    
# Función para validar que el modelo y la versión no existe ya para ese usuario
def model_version_not_exists(username, model_name, model_version):
    try:
        prefix = f"models/{username}/{model_name}/"
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            for obj in response['Contents']:
                parts = obj['Key'].split('/')
                if len(parts) > 3 and parts[3] == model_version:
                    return False
        return True
    except NoCredentialsError:
        st.error("Credenciales de AWS no encontradas.")
        return False
    except ClientError as e:
        st.error(f"Error al verificar la versión del modelo: {e}")
        return False

# Función para guardar modelo y metadatos
def save_model(model_name, model_version, model_description, model_file, script_file, username, model_type, symbol, base_currency, frequency, requirements):
    if model_type == 'SCRIPTING':
        s3_key_model = ""
    else:
        s3_key_model = f"models/{username}/{model_name}/{model_version}/{model_file.name}"
    s3_key_script = f"models/{username}/{model_name}/{model_version}/{script_file.name}"
    metadata = {
        "description": model_description,
        "model_type": model_type,
        "symbol": symbol,
        "base_currency": base_currency,
        "frecuency": frequency,
        "requirements":requirements,
        "ratings": []
    }
    try:
        if model_version_not_exists(username, model_name, model_version):
            if model_type != 'SCRIPTING':
                s3_client.upload_fileobj(model_file, bucket_name, s3_key_model)
            s3_client.upload_fileobj(script_file, bucket_name, s3_key_script)
            s3_client.put_object(Bucket=bucket_name, Key=f"models/{username}/{model_name}/{model_version}/metadata.json", Body=json.dumps(metadata))
            st.session_state.save_model = "save"
            st.success(f"Modelo {model_name} versión {model_version} subido exitosamente.")
            script_location = f"s3://{bucket_name}/models/{username}/{model_name}/{model_version}/{script_file.name}"
            if model_type=="SCRIPTING":
                model_location = "empty"
            else:
                model_location = f"s3://{bucket_name}/models/{username}/{model_name}/{model_version}/{model_file.name}"
            job_name = f"{username}_{model_name}_{model_version}_job"
            lambda_payload = {
                'script_location': script_location,
                'model_location': model_location,
                'job_name': job_name,
                'model_type': model_type,
                'symbol': symbol,
                'base_currency': base_currency,
                'frecuency': frequency,
                'requirements': requirements
                }
            response = lambda_client.invoke(
                FunctionName=f"arn:aws:lambda:us-east-1:{account_id}:function:{lambda_name}",
                InvocationType="Event",
                Payload=json.dumps(lambda_payload)
            )
            print("Modelo guardado exitosamente y job de Glue creado.")
        else:
            st.session_state.save_model = "exist"
            print(f"La versión {model_version} del modelo {model_name} ya existe y no puede ser creada.")
    except NoCredentialsError:
        st.error("Credenciales de AWS no encontradas.")
    except ClientError as e:
        st.error(f"Error al subir el modelo: {e}")

# Función para eliminar modelo y metadatos
def delete_model(username, model_name, model_version):
    try:
        prefix = f"models/{username}/{model_name}/{model_version}/"
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
        st.success(f"Modelo {model_name} versión {model_version} eliminado exitosamente.")
    except NoCredentialsError:
        print("error")
        st.error("Credenciales de AWS no encontradas.")
    except ClientError as e:
        print("error2")
        st.error(f"Error al eliminar el modelo: {e}")

def check_s3_folder_exists(bucket_name, folder_name):
    s3_client = boto3.client('s3')
    
    # Ensure the folder_name ends with a '/'
    if not folder_name.endswith('/'):
        folder_name += '/'

    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=folder_name,
            MaxKeys=1
        )
        
        # If the response contains any contents, the folder exists
        return 'Contents' in response
    
    except ClientError as e:
        print(f"Error checking S3 folder: {e}")
        return False

#Función de evaluación base
def get_basic_evaluation(dataframe, initial_balance=10000):
    
    dataframe['DATETIME'] = pd.to_datetime(dataframe['DATETIME'])
    balance = initial_balance
    dataframe['Portfolio Value'] = balance  # Start portfolio value with initial balance

    # Ensuring correct order and resetting the index
    dataframe.sort_values(by='DATETIME', inplace=True)
    dataframe.reset_index(drop=True, inplace=True)

    # Loop through the dataframe and adjust portfolio value based on the SIGNAL
    for i in range(1, len(dataframe)):
        prev_close = dataframe['CLOSE'].iloc[i-1]
        curr_close = dataframe['CLOSE'].iloc[i]

        # If buy signal (1), increase portfolio by the percentage change in price (long position)
        if dataframe['SIGNAL'].iloc[i-1] == 1:
            balance *= curr_close / prev_close
        
        # If sell signal (-1), adjust the portfolio based on the inverse of the price change (short position)
        elif dataframe['SIGNAL'].iloc[i-1] == -1:
            balance *= prev_close / curr_close  # Profit from falling prices, loss from rising prices
        
        # No adjustment for Signal == 0 (stay in cash)

        # Update the portfolio value after each iteration
        dataframe.at[i, 'Portfolio Value'] = balance

    # Calculate total returns
    final_balance = balance
    total_return = (final_balance - initial_balance) / initial_balance * 100

    # Summarize backtest results
    backtest_results = {
        "Initial Balance": initial_balance,
        "Final Balance": round(float(final_balance), 2),
        "Total Return (%)": round(float(total_return), 2)
    }

    return backtest_results, dataframe

# Second function: Advanced Evaluation
def get_advanced_evaluation(dataframe):
    dataframe['DATETIME'] = pd.to_datetime(dataframe['DATETIME'])
    # Ensuring correct order and resetting the index
    dataframe.sort_values(by='DATETIME', inplace=True)
    dataframe.reset_index(drop=True, inplace=True)

    # Calculate daily returns based on portfolio value
    dataframe['Returns'] = dataframe['Portfolio Value'].pct_change()

    # Financial Metrics
    risk_free_rate = 0.01  # Assume a 1% risk-free rate
    sharpe_ratio = (dataframe['Returns'].mean() - risk_free_rate / 252) / dataframe['Returns'].std() * np.sqrt(252)

    downside_returns = dataframe[dataframe['Returns'] < 0]['Returns']
    sortino_ratio = (dataframe['Returns'].mean() - risk_free_rate / 252) / downside_returns.std() * np.sqrt(252)

    winning_trades = dataframe[dataframe['Returns'] > 0]['Returns'].count()
    total_trades = dataframe['Returns'].count()
    win_ratio = winning_trades / total_trades * 100

    dataframe['Cumulative Max'] = dataframe['Portfolio Value'].cummax()
    dataframe['Drawdown'] = dataframe['Portfolio Value'] / dataframe['Cumulative Max'] - 1
    max_drawdown = dataframe['Drawdown'].min()

    cumulative_return = (dataframe['Portfolio Value'].iloc[-1] / dataframe['Portfolio Value'].iloc[0]) - 1

    # Displaying the financial metrics
    financial_metrics = {
        "Sharpe Ratio": round(float(sharpe_ratio), 2),
        "Sortino Ratio": round(float(sortino_ratio), 2),
        "Win Ratio (%)": round(float(win_ratio), 2),
        "Max Drawdown (%)": round(float(max_drawdown * 100), 2),
        "Cumulative Return (%)": round(float(cumulative_return * 100), 2)
    }

    return financial_metrics

# Third function: Reduction Function
def reduction_function(dataframe):
    dataframe['DATETIME'] = pd.to_datetime(dataframe['DATETIME'])
    # Ensuring correct order and resetting the index
    dataframe.sort_values(by='DATETIME', inplace=True)
    dataframe.reset_index(drop=True, inplace=True)

    # Aggregate by day, taking the last value for 'CLOSE' and 'Portfolio Value' at the end of each day
    dataframe = dataframe.resample('D', on='DATETIME').agg({'CLOSE': 'last', 'Portfolio Value': 'last'}).reset_index()

    return dataframe

def plot_portfolio_evolution(dataframe, symbol, base_currency):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.io as pio

    # Set renderer to 'browser' to open the plot in a web browser
    pio.renderers.default = 'browser'

    # Create a figure with two y-axes (BTC price on the left and portfolio value on the right)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add the BTC Price trace
    fig.add_trace(
        go.Scatter(x=dataframe['DATETIME'], y=dataframe['CLOSE'],
                name=f'{symbol} Price', line=dict(color='blue'), opacity=0.6),
        secondary_y=False,  # This specifies the left y-axis
    )

    # Add the Portfolio Value trace
    fig.add_trace(
        go.Scatter(x=dataframe['DATETIME'], y=dataframe['Portfolio Value'],
                name='Portfolio Value', line=dict(color='green'), opacity=0.6),
        secondary_y=True,  # This specifies the right y-axis
    )

    # Customize the layout and remove the horizontal grid lines
    fig.update_layout(
        title=f'{symbol} Last Closing Price vs Portfolio Value Evolution',
        title_x=0.5,  # Center the title
        xaxis_title='Date',
        yaxis_title=f'{symbol} Last Closing Price ({base_currency})',
        yaxis=dict(title=f'{symbol} Last Closing Price ({base_currency})', titlefont=dict(color='blue'), tickfont=dict(color='blue'),
                showgrid=False),  # Disable grid for the y-axis (BTC Price)
        yaxis2=dict(title=f'Portfolio Value ({base_currency})', titlefont=dict(color='green'), tickfont=dict(color='green'),
                    showgrid=False),  # Disable grid for the y-axis (Portfolio Value)
        xaxis=dict(showgrid=False, hoverformat='%Y-%m-%d'),  # Display full date (YYYY-MM-DD) in hover
        template='ggplot2',  # Parece que no funciona con streamlit plot :/
        legend=dict(x=0.02, y=0.98, font=dict(color='black'), bgcolor='rgba(255,255,255,0)'),  # Interactive legend
        height=600,
        width=1000,
    )

    # Customize x-axis (Date)
    fig.update_xaxes(tickformat="%b %Y", tickangle=45)

    # Return the plot
    return fig

# Sistema de login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Iniciar Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        if user_auth(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Inicio de sesión exitoso")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
else:
    # Menú lateral
    menu = st.sidebar.selectbox("Menú", ["Marketplace de Modelos", "Zona Personal"])

    if menu == "Marketplace de Modelos":
        st.title("Marketplace de Modelos")

        # Campos de entrada para los filtros
        col1, col2 = st.columns(2)
        with col1:
            filter_model_name = st.text_input("Filtrar por Nombre de Modelo")
        with col2:
            filter_user = st.text_input("Filtrar por Usuario")
        filter_rating = st.slider("Filtrar por Valoración Mínima", 0, 5, 0)

        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="models/")
            if 'Contents' in response:
                models = []
                for obj in response['Contents']:
                    model_key = obj['Key']
                    parts = model_key.split('/')
                    if len(parts) >= 4 and parts[-1] != "metadata.json" and (parts[-1][-3:]==".py" or parts[-1][-6:]==".ipynb"):
                        username = parts[1]
                        model_name = parts[2]
                        model_version = parts[3]
                        metadata_key = f"models/{username}/{model_name}/{model_version}/metadata.json"
                        metadata_response = s3_client.get_object(Bucket=bucket_name, Key=metadata_key)
                        metadata = json.loads(metadata_response['Body'].read().decode('utf-8'))
                        average_rating = sum(metadata["ratings"]) / len(metadata["ratings"]) if metadata["ratings"] else "-"                            

                        # Aplicar filtros
                        if average_rating == "-":
                            avg_rating = 0
                        else:
                            avg_rating = round(float(average_rating))
                        if (not filter_model_name or filter_model_name.lower() in model_name.lower()) and \
                        (not filter_user or filter_user.lower() in username.lower()) and \
                        (avg_rating >= filter_rating):
                            models.append({
                            "username": username,
                            "model_name": model_name,
                            "model_version": model_version,
                            "average_rating": average_rating,
                            "metadata_key": metadata_key,
                            "metadata": metadata
                            })

                if not models:
                    st.info("No hay ningún modelo, publica el primero.")
                else:
                    # Paginación
                    page_size = 5
                    total_pages = int(len(models) / page_size) + 1
                    page = st.sidebar.number_input("Página", min_value=1, max_value=total_pages, step=1)

                    start_idx = (page - 1) * page_size
                    end_idx = start_idx + page_size
                    models_to_display = models[start_idx:end_idx]

                    # Mostrar modelos en una tabla expandible
                    for model in models_to_display:
                        with st.expander(f"{model['model_name']} - {model['model_version']} -  Valoración: {'⭐' * int(model['average_rating']) if model['average_rating'] != '-' else '-'}"):
                            st.markdown(f"**Usuario:** {model['username']}")
                            
                            # Pongo info en una sola fila
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"Símbolo: {model['metadata']['symbol']}")
                            with col2:
                                st.write(f"Moneda: {model['metadata']['base_currency']}")
                            with col3:
                                st.write(f"Moneda: {model['metadata']['frecuency']}")

                            #Mostramos descripción
                            st.write(f"Descripción: {model['metadata']['description']}")

                            #Carga del output.csv
                            if check_s3_folder_exists(bucket_name, f"models/{model['username']}/{model['model_name']}/{model['model_version']}/output"):
                                output_key = f"models/{model['username']}/{model['model_name']}/{model['model_version']}/output/output.csv"
                                
                                #load csv to a dataframe from output_key
                                response = s3_client.get_object(Bucket=bucket_name, Key=output_key)
                                df = pd.read_csv(io.BytesIO(response['Body'].read()))
                                
                                #Calculating backtesting
                                backtest_results, dataframe = get_basic_evaluation(df)

                                #Calculating metrics 
                                financial_metrics = get_advanced_evaluation(dataframe)
                                
                                #Calculating plot
                                reduced_df = reduction_function(df)
                                fig = plot_portfolio_evolution(reduced_df, model['metadata']['symbol'], model['metadata']['base_currency'])

                                st.plotly_chart(fig, use_container_width=True)
                                st.write('*Resultado Backtesting*:', backtest_results)
                                st.write('*Métricas Financieras*:', financial_metrics)


                            rating = st.slider("Valorar el modelo", 1, 5, key=f"rating_{model['model_name']}_{model['model_version']}")
                            if st.button("Enviar Valoración", key=f"submit_rating_{model['model_name']}_{model['model_version']}"):
                                model['metadata']['ratings'].append(rating)
                                s3_client.put_object(Bucket=bucket_name, Key=model['metadata_key'], Body=json.dumps(model['metadata']))
                                st.success("Valoración enviada exitosamente.")
                                st.rerun()
            else:
                st.info("No hay ningún modelo, publica el primero.")
        except ClientError as e:
            st.error(f"Error al listar los modelos: {e}")

    elif menu == "Zona Personal":
        if 'save_model' not in st.session_state:
                st.session_state['save_model'] = 'init'
        st.title("Tus Modelos")
        if st.button("Crear Nuevo Modelo"):
            st.session_state.show_modal = True
        if st.session_state.save_model == "save":
            st.success(f"Modelo subido exitosamente.")
            st.session_state.save_model = ""
        if st.session_state.save_model == "exist":
            st.error(f"La versión del modelo ya existe y no puede ser creada.")
            st.session_state.save_model = ""
        if st.session_state.get("show_modal"):
            with st.form(key='model_form'):
                model_name = st.text_input("Nombre del Modelo")
                model_version = st.text_input("Versión del Modelo")
                model_description = st.text_area("Descripción del Modelo")
                model_type = st.selectbox("Tipo de Modelo", ["SCRIPTING", "ML SCKIT-LEARN"])
                model_symbol = st.selectbox("Symbol", ["ETHUSD","XDGUSD","USDTUSD","LINKUSD","XBTUSD"])
                model_base_currency = st.selectbox("Base Currency",["USD"])
                model_frequency = st.selectbox("Frecuencia", ["15min", "1day"])
                model_requirements = st.text_area("Librerías necesarias para el script. DEBEN ESCRIBIRSE EN MINÚSCULA, EN UNA LINEA Y SEPARADOS POR COMAS")
                model_file = st.file_uploader("Selecciona un archivo de modelo SOLAMENTE si es de tipo ML SCIKIT-LEARN", type=["pkl", "h5", "pt", "onnx", "joblib"])
                script_file = st.file_uploader("Selecciona un archivo de script (.py)", type=["py"])
                col1, col2, _ = st.columns([1, 1, 3])  # Ajustar el ancho de las columnas
                with col1:
                    submit_button = st.form_submit_button(label='Subir Modelo')
                    if submit_button:
                        if model_type == 'SCRIPTING':
                            if model_name and model_version and model_description and script_file and model_type and model_symbol and model_base_currency and model_frequency:
                                model_file = ''
                                save_model(model_name, model_version, model_description, model_file, script_file, st.session_state.username, model_type, model_symbol, model_base_currency, model_frequency, model_requirements)
                                
                                st.session_state.show_modal = False
                                st.rerun()
                            else:
                                st.error("Por favor, completa todos los campos.")
                        else:
                            if model_name and model_version and model_description and model_file and script_file and model_type and model_symbol and model_base_currency and model_frequency:
                                save_model(model_name, model_version, model_description, model_file, script_file, st.session_state.username, model_type, model_symbol, model_base_currency, model_frequency, model_requirements)
                                
                                st.session_state.show_modal = False
                                st.rerun()
                            else:
                                st.error("Por favor, completa todos los campos.")
                with col2:
                    cancel_submit_button = st.form_submit_button(label="Cancelar")
                    if cancel_submit_button:
                        st.session_state.show_modal = False
                        st.rerun()

        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f"models/{st.session_state.username}/")
            if 'Contents' in response:
                for obj in response['Contents']:
                    model_key = obj['Key']
                    parts = model_key.split('/')
                    if len(parts) >= 4 and parts[-1] != "metadata.json" and (parts[-1][-3:]==".py" or parts[-1][-6:]==".ipynb"):
                        model_name = parts[2]
                        model_version = parts[3]
                        metadata_key = f"models/{st.session_state.username}/{model_name}/{model_version}/metadata.json"
                        metadata_response = s3_client.get_object(Bucket=bucket_name, Key=metadata_key)
                        metadata = json.loads(metadata_response['Body'].read().decode('utf-8'))
                        average_rating = sum(metadata["ratings"]) / len(metadata["ratings"]) if metadata["ratings"] else "-"
                        with st.expander(f"{model_name} - v.{model_version}"):
                            st.write(f"Descripción: {metadata['description']}")
                            st.markdown(f"**Valoración Media:** <span style='color: yellow;'>{'⭐' * int(average_rating) if average_rating != '-' else '-'}</span>", unsafe_allow_html=True)
                            if st.button("🗑️ Eliminar", key=f"delete_{model_name}_{model_version}"):
                                st.session_state[f"confirm_delete_{model_name}_{model_version}"] = True

                            if st.session_state.get(f"confirm_delete_{model_name}_{model_version}", False):
                                st.warning(f"¿Estás seguro de que quieres eliminar el modelo {model_name} versión {model_version}?")
                                col1, col2, _ = st.columns([1, 1, 9])  # Ajustar el ancho de las columnas
                                with col1:
                                    if st.button("SI", key=f"confirm_delete_SI_{model_name}_{model_version}"):
                                        delete_model(st.session_state.username, model_name, model_version)
                                        st.session_state[f"confirm_delete_{model_name}_{model_version}"] = False
                                        st.rerun()
                                with col2:
                                    if st.button("NO", key=f"confirm_delete_NO_{model_name}_{model_version}"):
                                        st.session_state[f"confirm_delete_{model_name}_{model_version}"] = False
                                        st.rerun()
                                                
            else:
                st.info("No has publicado ningún modelo aún.")
        except ClientError as e:
            st.error(f"Error al listar los modelos: {e}")

    # Logout
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.success("Sesión cerrada exitosamente.")
        st.rerun()