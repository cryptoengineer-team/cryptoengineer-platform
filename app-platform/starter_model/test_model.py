import pandas as pd
from predict import predict

df=pd.DataFrame([[10, 20, 30],[20, 10, 30]])
print(df)
model_input=df.iloc[1,:]
print(model_input)

t3= predict(model_input)

print(t3)

import requests

"""
# TEST THE API de un modelo para predecir
#URL="https://hllngqp09e.execute-api.us-east-2.amazonaws.com/prod/predict"
URL="https://gdb6k0xxnj.execute-api.us-east-2.amazonaws.com/dev/predict"

response= requests.post(URL, json={"inputs": [[2,3,4,5]]})
"""
# TEST de API para crear una API-Lmabda para un modelo
#URL="https://hllngqp09e.execute-api.us-east-2.amazonaws.com/prod/predict"
URL="https://1uxn3ixz7j.execute-api.us-east-2.amazonaws.com/pro/deploy"

body= {
  "body": {
    "user": "hector",
    "model": "skl_iris_predict",
    "version": "1"
  }
}

response= requests.post(URL, json=body)

print(response.status_code)
print(response.reason)
print(response.content)
print(response.text)
print(response.headers)
print(response.request)
print(response.json())