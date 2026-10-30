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
