import json
import mlflow
import os
import numpy as np

#import boto3
#import botocore
#import pickle

# Set the tracking URI server
#print(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_tracking_uri(uri=os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
print("Set tracking uri")
# Load the model
loaded_model = mlflow.pyfunc.load_model(os.getenv("MODEL_URI"))
#print("Model Loaded")

def lambda_handler(event, context):
    # TODO implement
    # Converto the inputs serialized to dict
    #inputs_json= json.loads(event)
    
    # Get the current tracking uri
    print("Get tracking ")
    tracking_uri = mlflow.get_tracking_uri()
    print(f"Current tracking uri: {tracking_uri}")    

    #print(os.getenv("MODEL_URI"))
    loaded_model = mlflow.pyfunc.load_model(os.getenv("MODEL_URI"))
    # download model file from S3 into /tmp folder
    print("Model Loaded")
   
    # Create an array of arrays
    X=np.array([np.array(xi) for xi in event['inputs']])

    print(X)
    predictions = loaded_model.predict(X)
    
    return {
        'statusCode': 200,
        'body': json.dumps(predictions.tolist())
    }
