variable "AWS_ACCESS_KEY_ID" {
  type    = string
}

variable "AWS_SECRET_ACCESS_KEY" {
  type    = string
}

variable "AWS_SESSION_TOKEN" {
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
   default = ["datalake", "gluejobs-py-modules", "datalake/forex", "datalake/commodities"]
}

variable "MYLOCALIP" {
  description = "The IP address to access from."
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
  default     = ["us-east-1a", "us-east-1b"]
}

variable "tracker_name" {
  type        = string
  description = "Experiment Tracking tool Name"
  default     = "mlflow"
}

variable "tracker_image" {
  description = "Docker image url used in ECS task for Mlflow server."
  default     = "212430227630.dkr.ecr.us-east-1.amazonaws.com/mlflow-production-repository"
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

variable "cidr" {
  description = "The CIDR block for the VPC."
  default     = "10.32.0.0/16"
}

variable "execution_role_arn" {
  description = "The CIDR block for the VPC."
  default     = "arn:aws:iam::212430227630:role/LabRole"
}
