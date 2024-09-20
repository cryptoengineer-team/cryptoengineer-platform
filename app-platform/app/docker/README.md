# Create a docker image containing Front Marketplace streamlit app and upload to AWS ECR repository

## Instructions

- Create an AWS ECR repository
Manually in AWS Console or using the AWS Cli

212430227630.dkr.ecr.us-east-1.amazonaws.com/cryptoengineer/front_marketplace

- build the docker image to upload to AWS ECR
```bash
docker build --platform linux/amd64 -t frontmarketplace:latest .
```

- Connect to AWS ECR
```bash
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ECR_ACCOUNT}
```

- Tag the image 
```bash
docker tag frontmarketplace:latest ${AWS_ECR_ACCOUNT}/cryptoengineer/front_marketplace
```

-Push the image to AWS ECR
```bash
docker push ${AWS_ECR_ACCOUNT}/cryptoengineer/front_marketplace
```

## CREATE ECS Cluster and Service to run our Front Marketplace
- Crear un cluster
    - Asignarle un namespace
- Crear una task definition
    - Asignarle el contenedor IMAGE URI anterior
    - Asignarle CPU and RAM
- Crear un service para la task definition anterior
    - Launch type
    - Fargate
    - Service
    - Service name: front-marketplace
    - Configuracion por defecto de networking: Default VPC and subnets y asignado al grupo de seguridad por defecto.