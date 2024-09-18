import mlflow
import pandas as pd
from predict import predict

from mlflow.models.signature import infer_signature, set_signature


def report_signature_info(input_data, output_data=None, params=None):
    inferred_signature = infer_signature(input_data, output_data, params)

    report = f"""
The input data: \n\t{input_data}.
The data is of type: {type(input_data)}.
The inferred signature is:\n\n{inferred_signature}
"""
    print(report)

# Set our tracking server uri for logging
mlflow.set_tracking_uri(uri="http://localhost:5000")

# Create a new MLflow Experiment
mlflow.set_experiment("custom_fun_test")

print("Registering the model")
with mlflow.start_run():
    print("Logging the model")

    model_info = mlflow.pyfunc.log_model(
        artifact_path="custom_fun_model",
        python_model=predict,
        input_example=pd.DataFrame([[10, 20, 30]]),
        pip_requirements=[
            "pandas==2.2.2",
            "numpy==1.26.1",
        ],
        registered_model_name=f"custom_fun_model",
    )


print("Registered the model")