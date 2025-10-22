# Variables for Skyrchitect AWS Deployment

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "skyrchitect"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "bedrock_model_id" {
  description = "AWS Bedrock model ID for Claude Sonnet 4"
  type        = string
  default     = "us.anthropic.claude-sonnet-4-20250514-v1:0"
}

variable "backend_task_count" {
  description = "Number of backend ECS tasks to run"
  type        = number
  default     = 2
}
