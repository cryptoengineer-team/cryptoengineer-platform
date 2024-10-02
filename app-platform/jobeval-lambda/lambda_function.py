import json
import boto3

account = "212430227630"
role_glue = "LabRole"
bucket_name = "cryptoengineer"
wrapper_script_location = "s3://aws-glue-assets-212430227630-us-east-1/scripts/template_job_model-3.py"

def lambda_handler(event, context):
    glue_client = boto3.client('glue')
    
    # Parámetros del evento
    script_location = event['script_location']
    model_location = event['model_location']
    job_name = event['job_name']
    model_type = event['model_type']
    symbol = event['symbol']
    base_currency = event['base_currency']
    frecuency = event['frecuency']
    requirements = event['requirements']
    
    # Convertir el string de requirements en una lista, quitar espacios y saltos de linea y filtrar la librería cryptoengineer
    requirements_cleaned = requirements.replace('\n', '').replace('\r', '').replace(' ', '')
    requirements_list = requirements_cleaned.split(',')
    filtered_requirements = [lib for lib in requirements_list if not lib.startswith('cryptoengineersdk')]
    filtered_requirements_str = ','.join(filtered_requirements)

    mode_script_glue = 'SCRIPT'
    
    # Crear el job de Glue
    response = glue_client.create_job(
        Name=job_name,
        Role=f'arn:aws:iam::{account}:role/{role_glue}',
        Command={
            'Name': 'glueetl',
            'ScriptLocation': wrapper_script_location,
            'PythonVersion': '3'
        },
        MaxRetries=0,
        Timeout=10,
        MaxCapacity=2.0,
        GlueVersion='4.0',

        JobMode=mode_script_glue,
        DefaultArguments={
            "--TempDir": f"s3://{bucket_name}/temp/",
            "--additional-python-modules": filtered_requirements_str,  
            "--extra-py-files": f"{script_location},s3://cryptoengineer/gluejobs-py-modules/cryptoengineersdk-1.0.1-py3-none-any.whl",
            "--model_location": model_location,
            "--script_location": script_location,
            "--model_type": model_type,
            "--base_currency": base_currency,
            "--symbol": symbol,
            "--frequency": frecuency
        }
        
    )
    
    # Crear el trigger para ejecutar el job cada domingo a las 8 de la mañana
    glue_client.create_trigger(
        Name=f"{job_name}_trigger",
        Type='SCHEDULED',
        Schedule='cron(0 8 ? * 1 *)',
        Actions=[{
            'JobName': job_name
        }],
        StartOnCreation=True
    )
    
    # Desencadenamos el job por primera vez para generar el output
    glue_client.start_job_run(JobName=job_name)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Job de Glue creado exitosamente')
    }
