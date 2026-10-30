variable "aws_region" {
  description = "Region for ECR; provisioning may incur charges."
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Prefix for AWS resources."
  type        = string
  default     = "cloudforge"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,24}$", var.project_name))
    error_message = "Use lowercase letters, numbers and dashes, starting with a letter (3-25 chars)."
  }
}

variable "github_repository" {
  description = "Exact GitHub owner/repo permitted to use the OIDC role."
  type        = string
  default     = "eddy235/CloudForge"
}

variable "github_oidc_provider_arn" {
  description = "ARN of an existing, reviewed AWS GitHub OIDC provider. Empty disables the push role."
  type        = string
  default     = ""
  validation {
    condition     = var.github_oidc_provider_arn == "" || can(regex("^arn:aws:iam::[0-9]{12}:oidc-provider/token[.]actions[.]githubusercontent[.]com$", var.github_oidc_provider_arn))
    error_message = "Use the ARN of the AWS IAM provider token.actions.githubusercontent.com or leave empty."
  }
}
