terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.50"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region     = "${var.AWS_REGION}"
  access_key = "${var.AWS_ACCESS_KEY_ID}"
  secret_key = "${var.AWS_SECRET_ACCESS_KEY}"
  token = "${var.AWS_SESSION_TOKEN}"
}

# Create the ECS cluster
resource "aws_ecs_cluster" "aws-ecs-cluster" {
  name = "${var.tracker_name}-${var.app_environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.tracker_name}-ecs"
    Environment = var.app_environment
  }
}

data "template_file" "env_vars" {
  template = file("env_vars.json")

  vars = {
    aws_access_key_id     = var.AWS_ACCESS_KEY_ID
    aws_secret_access_key = var.AWS_SECRET_ACCESS_KEY
    aws_region_name       = var.AWS_REGION
    aws_bucket_name       = var.AWS_BUCKET_NAME
    # lambda_func_arn = "${aws_lambda_function.terraform_lambda_func.arn}"
    # lambda_func_name = "${aws_lambda_function.terraform_lambda_func.function_name}"
    ec2_subnet_id           = aws_subnet.public[0].id
  }
}

// To delete an existing log grou, run the cli command:
// aws logs delete-log-group --log-group-name app-name-production-logs
resource "aws_cloudwatch_log_group" "log-group" {
  name = "${var.tracker_name}-${var.app_environment}-logs"

  tags = {
    Application = var.tracker_name
    Environment = var.app_environment
  }
}

resource "aws_ecs_task_definition" "aws-ecs-task" {
  family = "${var.tracker_name}-task"

  container_definitions = <<DEFINITION
  [
    {
      "name": "${var.tracker_name}-${var.app_environment}-container",
      "image": "${var.tracker_image}",
      "environment": ${data.template_file.env_vars.rendered},
      "essential": true,
      "mountPoints": [
        {
          "readOnly": false,
          "containerPath": "/mlflow",
          "sourceVolume": "${var.tracker_name}-fs"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "${aws_cloudwatch_log_group.log-group.id}",
          "awslogs-region": "${var.AWS_REGION}",
          "awslogs-stream-prefix": "${var.tracker_name}-${var.app_environment}"
        }
      },
      "portMappings": [
        {
          "containerPort": 5000,
          "hostPort": 5000
        }
      ],
      "cpu": ${var.tracker_task_cpu},
      "memory": ${var.tracker_task_memory},
      "networkMode": "awsvpc",
      "ulimits": [
        {
          "name": "nofile",
          "softLimit": 16384,
          "hardLimit": 32768
        }
      ]
    }    
  ]
  DEFINITION

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = var.tracker_task_memory
  cpu                      = var.tracker_task_cpu
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.execution_role_arn

  volume {
    name = "${var.tracker_name}-fs"

    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.file_system.id
      transit_encryption = "ENABLED"
    }
  }

  tags = {
    Name        = "${var.tracker_name}-ecs-td"
    Environment = var.app_environment
  }

  # depends_on = [aws_lambda_function.terraform_lambda_func]
}

data "aws_ecs_task_definition" "main" {
  task_definition = aws_ecs_task_definition.aws-ecs-task.family
}

resource "aws_ecs_service" "aws-ecs-service" {
  name                 = "${var.tracker_name}-${var.app_environment}-ecs-service"
  cluster              = aws_ecs_cluster.aws-ecs-cluster.id
  task_definition      = "${aws_ecs_task_definition.aws-ecs-task.family}:${max(aws_ecs_task_definition.aws-ecs-task.revision, data.aws_ecs_task_definition.main.revision)}"
  launch_type          = "FARGATE"
  scheduling_strategy  = "REPLICA"
  desired_count        = 1
  force_new_deployment = true

  network_configuration {
    subnets          = aws_subnet.public.*.id
    assign_public_ip = true
    security_groups = [
      aws_security_group.service_security_group.id,
      aws_security_group.load_balancer_security_group.id
    ]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.target_group.arn
    container_name   = "${var.tracker_name}-${var.app_environment}-container"
    container_port   = 5000
  }

  depends_on = [aws_lb_listener.listener]
}

resource "aws_security_group" "service_security_group" {
  vpc_id = aws_vpc.aws-vpc.id

ingress {
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    cidr_blocks     = ["${chomp(data.http.myip.response_body)}/32", "${var.MYLOCALIP}"]
    security_groups = [aws_security_group.load_balancer_security_group.id]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "${var.tracker_name}-service-sg"
    Environment = var.app_environment
  }
}

