import json
import requests
import pandas as pd
import numpy as np

def load_data(path: str):
    #Read a CSV file
    df = pd.read_csv(path, header=0)
    # Map y values
    df['variety'] = df['variety'].map({"Setosa": 0, "Versicolor": 1, "Virginica": 2})
    # Extract input values
    X = df.iloc[:,:-1].values
    y = df.iloc[:,-1].values

    print("Data Shape: ", df.shape)

    return X,y

def predict(X: np.ndarray):
    payload = json.dumps(
        {
            "inputs": X.tolist(),
        }
    )
    response = requests.post(
        url=f"{base_url}/invocations",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    return response.json()

if __name__ == "__main__":
    # Endpoint
    base_url='http://localhost:8080'
    #Read data
    X,y= load_data('iris.csv')

    data=X[0:10]
    print(data)
    print(type(data))

    response= predict(data)
    print(response)

    #print(df.head())
    #print(X[:10])
    #print(y[:10])
