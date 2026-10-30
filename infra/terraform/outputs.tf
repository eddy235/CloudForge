output "ecr_repository_url" {
  description = "Push destination; only populated after terraform apply."
  value       = aws_ecr_repository.nexusdesk.repository_url
}

output "github_oidc_role_arn" {
  description = "Set this as GitHub Actions variable AWS_ROLE_ARN when enabled."
  value       = length(aws_iam_role.github_ecr_push) > 0 ? aws_iam_role.github_ecr_push[0].arn : null
}

output "aws_account_id" {
  description = "AWS account being configured (for sanity checks)."
  value       = data.aws_caller_identity.current.account_id
}

output "apprunner_service_url" {
  description = "HTTPS service origin only after explicitly enabling and applying paid AWS App Runner runtime."
  value       = length(aws_apprunner_service.nexusdesk_demo) > 0 ? "https://${aws_apprunner_service.nexusdesk_demo[0].service_url}" : null
}

output "apprunner_service_arn" {
  description = "ARN used for AWS CLI pause/resume and service operations after the paid runtime is created."
  value       = length(aws_apprunner_service.nexusdesk_demo) > 0 ? aws_apprunner_service.nexusdesk_demo[0].arn : null
}

output "runtime_enabled" {
  description = "Whether paid App Runner resources are enabled in this Terraform configuration."
  value       = var.enable_runtime
}
