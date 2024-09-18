# mlflow models serve -m models:/model_iris/1 -p 8080 --no-conda
#mlflow models serve -m models:/linear_model/1 -p 8080 --no-conda
#mlflow models serve -m models:/custom_fun_model/1 -p 8080 --no-conda

#mlflow models predict -m runs:/<run_id>/model -i input.csv -o output.csv
# curl http://127.0.0.1:5000/invocations -H "Content-Type:application/json"  --data '{"inputs": [[1, 2], [3, 4], [5, 6]]}'

import json
import requests

#base_url='https://ominous-yodel-rrqp7qvg4jrf59w5-8080.app.github.dev'
base_url='http://localhost:8080'
payload = json.dumps(
    {
        "inputs": [[7, 3.2, 4.7],[7, 3.2, 4.7]], #[[7, 3.2, 4.7, 1.4]]
    }
)
response = requests.post(
    url=f"{base_url}/invocations",
    data=payload,
    headers={"Content-Type": "application/json"},
    #auth=("admin", "password")
)

print(response)
print(response.status_code)
print(response.content)
print(response.reason)
print(response.text)
print(response.url)