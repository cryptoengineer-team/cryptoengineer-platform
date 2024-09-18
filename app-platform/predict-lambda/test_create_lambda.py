import logging
import boto3
from lambda_wrapper import LambdaWrapper

logger = logging.getLogger(__name__)

def run_test(iam_role_arn, lambda_name, lambda_description, handler_name, package_type, deployment_package, time_out, env_vars):
    """
    Runs the scenario.

    :param lambda_client: A Boto3 Lambda client.
    :param iam_resource: A Boto3 IAM resource.
    :param basic_file: The name of the file that contains the basic Lambda handler.
    :param calculator_file: The name of the file that contains the calculator Lambda handler.
    :param lambda_name: The name to give resources created for the scenario, such as the
                        IAM role and the Lambda function.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("-" * 88)
    print("Welcome to the AWS Lambda getting started with functions demo.")
    print("-" * 88)

    lambda_client = boto3.client("lambda")
    iam_resource = boto3.resource("iam")
    
    wrapper = LambdaWrapper(lambda_client, iam_resource)

    print(f"Looking for function {lambda_name}...")
    function = wrapper.get_function(lambda_name)
    if function is None:
        # Create a lambda function based on container image
        print(f"...and creating the {lambda_name} Lambda function.")
        wrapper.create_function(
            lambda_name, lambda_description, handler_name, iam_role_arn, package_type, deployment_package,
            time_out, env_vars
        )
    else:
        print(f"Function {lambda_name} already exists.")
    print("-" * 88)


if __name__ == "__main__":
    iam_role_arn="arn:aws:iam::223817798831:role/service-role/predict_model-role-ynh9ez1d"
    lambda_name="test_sklearn_model"
    lambda_description="Return prediction from a sklearn model - Test"
    handler_name="lambda_function.lambda_handler"
    package_type="Image"
    time_out=180
    env_vars={'Variables': {"AWS_BUCKET_NAME": "cryptoengineer-app",
                            "AWS_MODEL_KEY": "mlflow/2/cf5d04ca121b4ffea859fd4816e440b1/artifacts/east2_model/model.pkl"
                            }
              }
    
    deployment_package="223817798831.dkr.ecr.us-east-2.amazonaws.com/sklearn_model@sha256:c8a0ec9666634f6089f895b13a7dfc45fd8d03508c392fcba8661ee9f04563f5"
        
    try:
        run_test(iam_role_arn,  lambda_name, lambda_description, handler_name, package_type, deployment_package, time_out, env_vars)       
    except Exception:
        logging.exception("Something went wrong with the test!")
# snippet-end:[python.example_code.lambda.Scenario_GettingStartedFunctions]
"""
aws lambda create-function \
  --function-name test_sklearn_model \
  --package-type Image \
  --code ImageUri=223817798831.dkr.ecr.us-east-2.amazonaws.com/sklearn_model:latest \
  --role arn:aws:iam::223817798831:role/service-role/predict_model-role-ynh9ez1d    
"""