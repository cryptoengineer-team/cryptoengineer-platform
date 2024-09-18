import pandas as pd
import mlflow
from mlflow.pyfunc import PythonModel

# Set our tracking server uri for logging
mlflow.set_tracking_uri(uri="http://localhost:5000")

# Create a new MLflow Experiment
mlflow.set_experiment("custom_model_test")

# Custom PythonModel class
class SimpleLinearModel(PythonModel):
    def predict(self, context, model_input):
        """
        Applies a simple linear transformation
        to the input data. For example, y = 2x + 3.
        """
        # Assuming model_input is a pandas DataFrame with one column
        return pd.DataFrame(2 * model_input + 3)

print("Registering the model")
with mlflow.start_run():
    print("Logging the model")
    model_info = mlflow.pyfunc.log_model(
        artifact_path="linear_model",
        python_model=SimpleLinearModel(),
        input_example=pd.DataFrame([10, 20, 30]),
        pip_requirements=[
            "pandas==2.2.2",
            "numpy==1.26.1",
        ],
        registered_model_name=f"linear_model",
    )
print("Registered the model")