variable "AWS_ACCESS_KEY_ID" {
  type    = string
}

variable "AWS_SECRET_ACCESS_KEY" {
  type    = string
}

variable "AWS_REGION" {
  type        = string
  description = "AWS Region"
}

variable "AWS_BUCKET_NAME" {
  type        = string
  description = "S3 bucket for our project"
}

variable "default_s3_content" {
   description = "The default content of the s3 bucket upon creation of the bucket"
   type = set(string)
   default = ["mlflow"]
}

variable "PROJECT_NAME" {
  type        = string
  description = "Application Project Name"
  default     = "cryptoengineer"
}

variable "MYLOCALIP" {
  description = "The IP address to access from."
}

variable "APP_PORT" {
  type        = string
  description = "Port Streamlit Application"
}

variable "MLFLOW_PORT" {
  type        = string
  description = "Port Mlflow Application"
}

variable "MLFLOW_TRACKING_URI" {
  type        = string
  description = "Mlflow server URI"
}

variable "MLFLOW_EXPERIMENT_NAME" {
  type        = string
  description = "Default Mlflow Experiment Name "
}

variable "app_environment" {
  type        = string
  description = "Application Environment"
  default     = "production"
}

variable "public_subnets" {
  description = "List of public subnets"
  default     = ["10.32.100.0/24", "10.32.101.0/24"]
}

variable "private_subnets" {
  description = "List of private subnets"
  default     = ["10.32.0.0/24", "10.32.1.0/24"]
}

variable "availability_zones" {
  description = "List of availability zones"
  default     = ["us-east-2a", "us-east-2b"]
}

variable "app_name" {
  type        = string
  description = "Application Name"
  default     = "cryptoengineer"
}

variable "docker_image" {
  description = "Docker image url used in ECS task."
  default     = "223817798831.dkr.ecr.us-east-2.amazonaws.com/cryptoengineer-repository"
  type        = string
}

variable "tracker_name" {
  type        = string
  description = "Experiment Tracking tool Name"
  default     = "mlflow"
}

variable "tracker_image" {
  description = "Docker image url used in ECS task for Mlflow server."
  default     = "223817798831.dkr.ecr.us-east-2.amazonaws.com/mlflow-repository"
  type        = string
}

variable "tracker_task_cpu" {
  description = "ECS task cpu"
  default     = 1024
}

variable "tracker_task_memory" {
  description = "ECS task memory"
  default     = 4096
}

variable "ecs_task_cpu" {
  description = "ECS task cpu"
  default     = 2048
}

variable "ecs_task_memory" {
  description = "ECS task memory"
  default     = 4096
}

variable "cidr" {
  description = "The CIDR block for the VPC."
  default     = "10.32.0.0/16"
}
