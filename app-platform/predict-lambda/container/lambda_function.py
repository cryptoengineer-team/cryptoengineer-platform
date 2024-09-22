import json
import os
import numpy as np

import boto3
import joblib

# download model file from S3 into /tmp folder
print("Client configuration")
# When lambda is not in private VPC
s3 = boto3.client('s3')
# When lambda is in private VPC
#s3 = boto3.client('s3', 'us-east-2', config=botocore.config.Config(s3={'addressing_style':'path'}))

bucket = os.environ['AWS_BUCKET_NAME']
key = os.environ['AWS_MODEL_KEY']
print(f"Download file {bucket} , {key}")
s3.download_file(bucket, key, '/tmp/model.pkl')
# LOAD MODEL
loaded_model = joblib.load('/tmp/model.pkl')
print("Model Loaded")

def lambda_handler(event, context):
    # Converto the inputs serialized to dict
    #inputs_json= json.loads(event)
    
    # Create an array of arrays
    
    print("Transforming input")
    inputs= None

    if (event['body']) and (event['body'] is not None):
        body = json.loads(event['body'])
        
        try:
            if (body['inputs']) and (body['inputs'] is not None):
                inputs = body['inputs']
        except KeyError:
            print('No inputs')

    if inputs:
        X=np.array([np.array(xi) for xi in inputs])

        print("Input Data:",X)
        predictions = loaded_model.predict(X)
        print("Predictions: ",predictions)  

        res= {
        'statusCode': 200,
        'body': json.dumps(predictions.tolist())
        }    
    else:
        res= {
            'statusCode': 400,
            'body': "No valid input data"
        }
    
    return res
