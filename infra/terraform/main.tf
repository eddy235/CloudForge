provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project   = "CloudForge"
      ManagedBy = "Terraform"
      Stage     = "learning"
    }
  }
}

data "aws_caller_identity" "current" {}

# v0.1 deliberately provisions only a container registry, not compute, ALB, or NAT.
resource "aws_ecr_repository" "nexusdesk" {
  name                 = "${var.project_name}/nexusdesk-demo"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "trim_old_images" {
  repository = aws_ecr_repository.nexusdesk.name
  policy     = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the ten newest images for demo builds"
      selection    = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

data "aws_iam_policy_document" "github_trust" {
  count = var.github_oidc_provider_arn == "" ? 0 : 1
  statement {
    sid     = "TrustOnlyMainBranchOfCloudForge"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [var.github_oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_ecr_push" {
  count              = var.github_oidc_provider_arn == "" ? 0 : 1
  name               = "${var.project_name}-github-ecr-push"
  assume_role_policy = data.aws_iam_policy_document.github_trust[0].json
}

data "aws_iam_policy_document" "ecr_push" {
  count = var.github_oidc_provider_arn == "" ? 0 : 1
  # This API always needs resource="*"; no other global AWS permissions.
  statement {
    sid       = "TokenForECRLoginOnly"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    sid     = "PushImagesToCloudForgeRepositoryOnly"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [aws_ecr_repository.nexusdesk.arn]
  }
}

resource "aws_iam_role_policy" "github_ecr_push" {
  count  = var.github_oidc_provider_arn == "" ? 0 : 1
  name   = "CloudForgeECRPushOnly"
  role   = aws_iam_role.github_ecr_push[0].id
  policy = data.aws_iam_policy_document.ecr_push[0].json
}
