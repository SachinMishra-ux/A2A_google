# ==============================================================================
# Terraform Blueprint: Production Deployment on Amazon Web Services (AWS)
# Services: ECS Fargate, Application Load Balancer (ALB), Secrets Manager, VPC
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Target AWS Region"
}

variable "gemini_api_key" {
  type        = string
  sensitive   = true
  description = "Google Gemini API Key for autonomous agents"
}

provider "aws" {
  region = var.aws_region
}

# 1. AWS Secrets Manager for Credentials
resource "aws_secretsmanager_secret" "gemini_key" {
  name                    = "a2a/gemini-api-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "gemini_key_val" {
  secret_id     = aws_secretsmanager_secret.gemini_key.id
  secret_string = var.gemini_api_key
}

# 2. ECS Cluster
resource "aws_ecs_cluster" "a2a_cluster" {
  name = "a2a-multiagent-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# 3. ECS Task Definition (Fargate Serverless)
resource "aws_ecs_task_definition" "a2a_task" {
  family                   = "a2a-gateway-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "a2a-gateway"
      image     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/a2a-system:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
        }
      ]
      secrets = [
        {
          name      = "GEMINI_API_KEY"
          valueFrom = aws_secretsmanager_secret.gemini_key.arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/a2a-gateway"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "gateway"
        }
      }
    }
  ])
}

# IAM Roles for ECS Execution & Task
resource "aws_iam_role" "ecs_execution_role" {
  name = "a2a-ecs-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name = "a2a-ecs-task-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}
