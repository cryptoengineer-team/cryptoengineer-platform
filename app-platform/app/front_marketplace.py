import streamlit as st
import boto3
import json
from botocore.exceptions import NoCredentialsError, ClientError
import requests

# Configuración de AWS
aws_access_key_id = st.secrets["default"]["aws_access_key_id"]
aws_secret_access_key = st.secrets["default"]["aws_secret_access_key"]
aws_session_token = st.secrets["default"]["aws_session_token"]

s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_session_token=aws_session_token)

lambda_client = boto3.client(
    'lambda',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_session_token=aws_session_token)

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
                model_location = ""
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
                            st.write(f"Descripción: {metadata['description']}")
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
                model_symbol = st.selectbox("Symbol", ["ETHUSD","XDGUSD","USDTUSD","LINKUSD","XBTUSD","IBEX35","Nikkei225","DAX","DowJones","EuroStoxx50","Nasdaq","SP500","USDCHF","USDJPY","USDEUR","USDGBP","BZUSD","CLUSD","NGUSD","GCUSD"])
                model_base_currency = st.selectbox("Base Currency",["USD"])
                model_frequency = st.selectbox("Frecuencia", ["15min", "1day"])
                model_requirements = st.text_area("Librerías necesarias para el script. DEBEN ESCRIBIRSE EN MINÚSCULA, EN UNA LINEA Y SEPARADOS POR COMAS")
                model_file = st.file_uploader("Selecciona un archivo de modelo SOLAMENTE si es de tipo ML SCIKIT-LEARN", type=["pkl", "h5", "pt", "onnx"])
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