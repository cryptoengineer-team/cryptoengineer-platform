#Streamlit APP Test CryptoEngineer

# Importación de paquetes: 
import streamlit as st 
#import pandas as pd 
#import numpy as np
from dotenv import load_dotenv
import os
import subprocess

from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

import mlflow
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient

def list_runs_and_models(tracking_url: str, experiment_name: str, model_name: str):
    # Set our tracking server uri for logging
	mlflow.set_tracking_uri(uri=tracking_url)

	client = MlflowClient()

    # Get experiment details
	experiment = client.get_experiment_by_name(experiment_name)
	if experiment is None:
        #print(f"Experiment '{experiment_name}' not found.")
		st.write(f"Experiment '{experiment_name}' not found.")
		return

	st.write(f"Listing runs for experiment: {experiment.name} (ID: {experiment.experiment_id})")
    
    # List all runs under the experiment
	runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    
	if not runs.empty:
		st.write("Experiment runs:")
		st.write(runs[['run_id', 'status', 'start_time', 'end_time', 'artifact_uri']])
	else:
		st.write(f"No runs found for experiment '{experiment_name}'.")

	st.write("Registered models and versions:")
    
	for mv in client.search_model_versions(f"name='{model_name}'"):
		st.write(f"Model: {mv.name}, version: {mv.version}, Run id: {mv.run_id}")

# Train a simple model
def train_and_register_model(tracking_url: str, exp_name: str, model_name: str):
    # Load the Iris dataset
	X, y = datasets.load_iris(return_X_y=True)

	# Split the data into training and test sets
	X_train, X_test, y_train, y_test = train_test_split(
		X, y, test_size=0.2, random_state=42
	)

	# Define the model hyperparameters
	params = {
		"solver": "lbfgs",
		"max_iter": 1000,
		"multi_class": "auto",
		"random_state": 8888,
	}

	# Train the model
	lr = LogisticRegression(**params)
	lr.fit(X_train, y_train)

	# Predict on the test set
	y_pred = lr.predict(X_test)

	# Calculate metrics
	accuracy = accuracy_score(y_test, y_pred)
 
	# Set our tracking server uri for logging
	mlflow.set_tracking_uri(uri=tracking_url)

	# Create a new MLflow Experiment
	mlflow.set_experiment(exp_name)

	# Start an MLflow run
	with mlflow.start_run():
		# Log the hyperparameters
		mlflow.log_params(params)

		# Log the loss metric
		mlflow.log_metric("accuracy", accuracy)

		# Set a tag that we can use to remind ourselves what this run was for
		mlflow.set_tag("Training Info", "Basic LR model for iris data")

		# Infer the model signature
		signature = infer_signature(X_train, lr.predict(X_train))

		# Log the model
		model_info = mlflow.sklearn.log_model(
			sk_model=lr,
			artifact_path=model_name,
			signature=signature,
			input_example=X_train,
			registered_model_name=model_name,
		)
  
	return model_info

def build_image(tracking_url: str, model_name: str, version: str):
    # Set our tracking server uri for logging
	mlflow.set_tracking_uri(uri=tracking_url)
	model_uri= f'models:/{model_name}/{version}'
	st.write(model_uri)
	#mlflow.models.build_docker(model_uri=model_uri, name=f'{model_name}-image', env_manager='conda')
	# mlflow models build-docker -m runs:/<run_id>/model -n <image_name>
	subprocess.run(["mlflow", "models", "build-docker", "-m", model_uri, "-n", f'{model_name}-image']) 
	
	return model_uri

# Función principal
def main():
	load_dotenv()

	st.set_page_config(page_title="Test App CryptoEngineer", page_icon="���")
	# DEFINE AQUÍ TU CODIGO: 
	# Pon un titulo a la app
	st.title("Test App CryptoEngineer")
	# Crea un formulario con st.form()
	with st.form("Datos para el entrenamiento"):
     
	# Pon un texto explicativo con st.text() o st.write()
		exp_name= st.text_input(label="Introduce Exp name:", value=os.getenv("MLFLOW_EXPERIMENT_NAME",""))
	# Recoge el exp name
		model_name= st.text_input(label="Introduce Model name:")
		version= st.text_input(label="Introduce Version:")

		calcular= st.form_submit_button("Entrenar y Registrar")
		listar= st.form_submit_button("Listar runs y models")
		imagen= st.form_submit_button("Crear docker image")

    # Si se pulsa el boton de listar
	if (listar):
		list_runs_and_models(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"), exp_name, model_name)
	# Con los datos, calcula el IMC (peso / altura(m) al cuadrado)
	# Cuando se pulse el boton del formulario, muestralo en pantalla
	if (calcular):
		model_info= train_and_register_model(os.getenv("MLFLOW_TRACKING_URI","http://mlflow:5000"), 
                               exp_name, model_name)
		# Muestra el resultado en pantalla
		st.write(model_info)
		print("Modelo entrenado y registrado")
	if (imagen):
		model_uri= build_image(os.getenv("MLFLOW_TRACKING_URI","http://mlflow:5000"),model_name,version)

	

# LLamada a la función principal 
if __name__ == '__main__':
	main()
