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

# v0.2 runtime remains disabled unless an operator deliberately chooses a
# billable deployment and provides both a real published image and secret.
variable "enable_runtime" {
  description = "Explicitly opt in to a paid App Runner service. FALSE by default."
  type        = bool
  default     = false
}

variable "runtime_image_tag" {
  description = "Immutable, 40-character CloudForge commit SHA of an image already published to ECR."
  type        = string
  default     = ""

  validation {
    condition     = var.runtime_image_tag == "" || can(regex("^[0-9a-f]{40}$", var.runtime_image_tag))
    error_message = "Use the 40-character lowercase commit SHA from an image actually published to ECR, or leave empty."
  }
}

variable "demo_secret_parameter_arn" {
  description = "ARN of an existing SSM SecureString for DJANGO_SECRET_KEY. Never put the secret value into Terraform state or .tfvars."
  type        = string
  default     = ""

  validation {
    condition     = var.demo_secret_parameter_arn == "" || can(regex("^arn:aws:ssm:[a-z0-9-]+:[0-9]{12}:parameter/[A-Za-z0-9_.\\/-]+$", var.demo_secret_parameter_arn))
    error_message = "Set an SSM Parameter Store parameter ARN or leave empty when runtime is disabled."
  }
}
