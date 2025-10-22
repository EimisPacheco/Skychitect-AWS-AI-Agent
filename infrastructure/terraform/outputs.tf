# Outputs for Skyrchitect AWS Deployment

output "frontend_url" {
  description = "CloudFront distribution URL for frontend"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "frontend_s3_bucket" {
  description = "S3 bucket name for frontend hosting"
  value       = aws_s3_bucket.frontend.id
}

output "backend_api_url" {
  description = "Application Load Balancer URL for backend API"
  value       = "http://${aws_lb.main.dns_name}"
}

output "ecr_repository_url" {
  description = "ECR repository URL for backend Docker images"
  value       = aws_ecr_repository.backend.repository_url
}

output "diagrams_s3_bucket" {
  description = "S3 bucket name for architecture diagrams storage"
  value       = aws_s3_bucket.diagrams.id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.backend.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for backend logs"
  value       = aws_cloudwatch_log_group.backend.name
}
