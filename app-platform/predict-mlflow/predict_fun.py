import mlflow
import os
import pandas as pd
import numpy as np
import json

from sklearn import datasets
from sklearn.model_selection import train_test_split


# Set the tracking URI server
mlflow.set_tracking_uri(uri=os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
print("Set tracking uri")
# Load the model
loaded_model = mlflow.pyfunc.load_model(os.getenv("MODEL_URI"))

def predict_dataframe(X: pd.DataFrame):
    # Generate the predictions
    predictions = loaded_model.predict(X)

    return predictions

def predict(events):
    # Converto the inputs serialized to dict
    inputs_json= json.loads(events)

    # Create an array of arrays
    X=np.array([np.array(xi) for xi in inputs_json['inputs']])

    print(X)
    predictions = loaded_model.predict(X)

    return predictions

if __name__ == "__main__":
    # Load the Iris dataset
    X, y = datasets.load_iris(return_X_y=True, as_frame=True)

    # Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    # Extract a sample    
    X_sample= X_test.sample(3)
    print(X_sample)

    # Serialize the inputs as a json string
    payload = json.dumps(
        {
            "inputs": X_sample.values.tolist(), #[[7, 3.2, 4.7, 1.4]]
        }
    )    
    # Get the predictions
    predictions = predict(payload)
    print(predictions)


    # Converto to json
    #json_event= X_sample.to_json(orient='records')
    #print(json_event)

    #data = pd.DataFrame(json_event, index=[0])
    #data = pd.DataFrame.from_dict(pd.json_normalize(json_event), orient='index')

    #print(data)

    ## Convert X_test validation feature data to a Pandas DataFrame
    #result = pd.DataFrame(X_test, columns=iris_feature_names)
    """
    print("Type X_test: ", type(X_sample))
    print("Shape X_test: ", X_sample.shape)
    print("X_test samples: ", X_sample)

    preds= predict(X_sample)

    print(preds)
    print(y_test[:3])
    """