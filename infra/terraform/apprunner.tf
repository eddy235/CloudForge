# v0.2: An optional managed AWS HTTPS runtime. All resources are gated behind
# enable_runtime=false by default. Never apply before reviewing billing.
#
# Run only the *fictional* NexusDesk demo. The application reads no database
# when DEMO_MODE=true; all operational paths remain denied by demo middleware.

data "aws_iam_policy_document" "apprunner_ecr_trust" {
  count = var.enable_runtime ? 1 : 0

  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apprunner_ecr_access" {
  count              = var.enable_runtime ? 1 : 0
  name               = "${var.project_name}-apprunner-ecr-access"
  assume_role_policy = data.aws_iam_policy_document.apprunner_ecr_trust[0].json
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_read" {
  count      = var.enable_runtime ? 1 : 0
  role       = aws_iam_role.apprunner_ecr_access[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

data "aws_iam_policy_document" "apprunner_runtime_trust" {
  count = var.enable_runtime ? 1 : 0

  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apprunner_runtime" {
  count              = var.enable_runtime ? 1 : 0
  name               = "${var.project_name}-apprunner-runtime"
  assume_role_policy = data.aws_iam_policy_document.apprunner_runtime_trust[0].json
}

data "aws_iam_policy_document" "apprunner_ssm" {
  count = var.enable_runtime ? 1 : 0

  statement {
    sid       = "ReadOnlyTheDemoSecretParameter"
    actions   = ["ssm:GetParameters"]
    resources = [var.demo_secret_parameter_arn]
  }
}

resource "aws_iam_role_policy" "apprunner_ssm" {
  count  = var.enable_runtime ? 1 : 0
  name   = "ReadDemoSecretParameterOnly"
  role   = aws_iam_role.apprunner_runtime[0].id
  policy = data.aws_iam_policy_document.apprunner_ssm[0].json
}

# One small provisioned instance and at most one active instance. App Runner
# still has provisioned-memory charges while idle; this is NOT a free service.
resource "aws_apprunner_auto_scaling_configuration_version" "demo_small" {
  count                           = var.enable_runtime ? 1 : 0
  auto_scaling_configuration_name = "${var.project_name}-demo-small"
  max_concurrency                 = 25
  min_size                        = 1
  max_size                        = 1
}

resource "aws_apprunner_service" "nexusdesk_demo" {
  count        = var.enable_runtime ? 1 : 0
  service_name = "${var.project_name}-nexusdesk-demo"

  source_configuration {
    auto_deployments_enabled = false

    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access[0].arn
    }

    image_repository {
      image_repository_type = "ECR"
      # ECR tags are immutable. Deploy exactly one reviewed Git commit image.
      image_identifier = "${aws_ecr_repository.nexusdesk.repository_url}:${var.runtime_image_tag}"

      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          NEXUSDESK_DEMO_MODE        = "true"
          DJANGO_DEBUG               = "false"
          # App Runner terminates public HTTPS before forwarding requests to
          # the container. Avoid redirecting its internal HTTP healthchecks.
          DJANGO_SECURE_SSL_REDIRECT = "false"
          DJANGO_ENABLE_HSTS         = "true"
          # The service's random hostname isn't known until after creation.
          # Restrict this *fictional demo* to AWS App Runner hostnames only.
          DJANGO_ALLOWED_HOSTS       = ".awsapprunner.com"
        }
        runtime_environment_secrets = {
          DJANGO_SECRET_KEY = var.demo_secret_parameter_arn
        }
      }
    }
  }

  instance_configuration {
    cpu               = "256"
    memory            = "512"
    instance_role_arn = aws_iam_role.apprunner_runtime[0].arn
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.demo_small[0].arn

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/health/"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  lifecycle {
    precondition {
      condition     = length(var.runtime_image_tag) == 40 && length(var.demo_secret_parameter_arn) > 0
      error_message = "To enable the paid runtime, set a published 40-character image commit SHA and a pre-created SSM SecureString parameter ARN."
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.apprunner_ecr_read,
    aws_iam_role_policy.apprunner_ssm
  ]
}
