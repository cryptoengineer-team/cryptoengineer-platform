import boto3

client = boto3.client('lambda')

bucket= "cryptoengineer-app"
model_key="mlflow/2/cf5d04ca121b4ffea859fd4816e440b1/artifacts/east2_model/model.pkl"

response = client.update_function_configuration(
    FunctionName='test_model',
    Timeout=180,
    Environment={
        'Variables': {
            'AWS_BUCKET_NAME': bucket,
            'AWS_MODEL_KEY':  model_key
        }
    }
)
print(response)