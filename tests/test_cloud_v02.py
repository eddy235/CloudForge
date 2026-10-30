"""v0.2 regression checks; never contacts or modifies an AWS account."""
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.smoke_cloud import verify

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class CloudDeploymentSecurityTests(unittest.TestCase):
    def test_paid_runtime_disabled_by_default(self):
        variables = read("infra/terraform/variables.tf")
        self.assertRegex(
            variables, r'(?s)variable "enable_runtime"\s*\{.*?default\s*=\s*false\s*\}'
        )
        self.assertRegex(
            variables, r'(?s)variable "runtime_image_tag"\s*\{.*?default\s*=\s*""'
        )
        self.assertRegex(
            variables, r'(?s)variable "demo_secret_parameter_arn"\s*\{.*?default\s*=\s*""'
        )

    def test_runtime_requires_published_image_and_managed_secret(self):
        hcl = read("infra/terraform/apprunner.tf")
        self.assertIn('count        = var.enable_runtime ? 1 : 0', hcl)
        self.assertIn('aws_ecr_repository.nexusdesk.repository_url', hcl)
        self.assertIn('var.runtime_image_tag', hcl)
        self.assertIn('runtime_environment_secrets', hcl)
        self.assertIn('DJANGO_SECRET_KEY = var.demo_secret_parameter_arn', hcl)
        self.assertIn('ssm:GetParameters', hcl)
        self.assertIn('ReadOnlyTheDemoSecretParameter', hcl)
        self.assertNotIn('aws_ssm_parameter', hcl)
        self.assertNotIn('password =', hcl)

    def test_app_runner_is_small_and_has_managed_https(self):
        hcl = read("infra/terraform/apprunner.tf")
        self.assertIn('resource "aws_apprunner_service"', hcl)
        self.assertIn('auto_deployments_enabled = false', hcl)
        self.assertIn('min_size                        = 1', hcl)
        self.assertIn('max_size                        = 1', hcl)
        self.assertIn('cpu               = "256"', hcl)
        self.assertIn('memory            = "512"', hcl)
        self.assertIn('path                = "/health/"', hcl)
        self.assertIn('DJANGO_SECURE_SSL_REDIRECT = "false"', hcl)
        self.assertIn('DJANGO_ENABLE_HSTS         = "true"', hcl)
        self.assertIn('NEXUSDESK_DEMO_MODE = "true"', hcl)
        self.assertIn('DJANGO_DEBUG        = "false"', hcl)
        self.assertIn('DJANGO_ALLOWED_HOSTS = ".awsapprunner.com,localhost,127.0.0.1"', hcl)

    def test_access_roles_have_service_scoped_trust(self):
        hcl = read("infra/terraform/apprunner.tf")
        self.assertIn('build.apprunner.amazonaws.com', hcl)
        self.assertIn('tasks.apprunner.amazonaws.com', hcl)
        self.assertIn('resources = [aws_ecr_repository.nexusdesk.arn]', hcl)
        self.assertIn('ecr:GetAuthorizationToken', hcl)
        self.assertIn('ecr:BatchGetImage', hcl)
        self.assertNotIn('AWSAppRunnerServicePolicyForECRAccess', hcl)
        self.assertNotIn('AdministratorAccess', hcl)
        self.assertNotIn('PowerUserAccess', hcl)

    def test_aws_deployment_cannot_run_in_ci(self):
        ci = read(".github/workflows/ci.yml")
        cloud = read(".github/workflows/cloud-smoke.yml")
        self.assertNotIn("terraform apply", ci)
        self.assertNotIn("configure-aws-credentials", ci)
        self.assertIn("workflow_dispatch:", cloud)
        self.assertNotRegex(cloud, r"(?m)^\s+push:")
        self.assertNotIn("configure-aws-credentials", cloud)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", cloud)

    def test_https_smoke_rejects_http_and_paths(self):
        for url in (
            "http://example.awsapprunner.com",
            "https://example.awsapprunner.com/demo/",
            "https://example.awsapprunner.com?status=1",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                verify(url)

    def test_synthetic_demo_verified_without_writes(self):
        seen = []

        def mocked_probe(origin, path, method="GET"):
            seen.append((path, method))
            if method != "GET":
                return 404, {}, b"blocked"
            if path == "/health/":
                return 200, {}, b'{"demo_mode":true,"status":"ok"}'
            if path == "/demo/":
                return 200, {
                    "Content-Security-Policy": "script-src 'none'; frame-ancestors 'none'",
                    "X-Content-Type-Options": "nosniff",
                }, b"NexusDesk SYNTHETIC DATA ONLY Asset lifecycle"
            if path == "/static/desk/style.css":
                return 200, {}, b"body {}"
            return 404, {}, b"blocked"

        with patch("scripts.smoke_cloud.probe", side_effect=mocked_probe):
            verify("https://demo.eu-west-1.awsapprunner.com")
        self.assertIn(("/admin/", "GET"), seen)
        self.assertIn(("/reports/export.csv", "POST"), seen)

    def test_smoke_rejects_private_route_exposure(self):
        def unsafe_probe(origin, path, method="GET"):
            if path == "/health/":
                return 200, {}, json.dumps({"demo_mode": True}).encode()
            if path == "/demo/":
                return 200, {
                    "Content-Security-Policy": "script-src 'none'; frame-ancestors 'none'",
                    "X-Content-Type-Options": "nosniff",
                }, b"NexusDesk SYNTHETIC DATA ONLY Asset lifecycle"
            if path == "/static/desk/style.css":
                return 200, {}, b"ok"
            if path == "/admin/":
                return 200, {}, b"admin exposed"
            return 404, {}, b"blocked"

        with patch("scripts.smoke_cloud.probe", side_effect=unsafe_probe):
            with self.assertRaisesRegex(AssertionError, "GET /admin/"):
                verify("https://demo.eu-west-1.awsapprunner.com")


if __name__ == "__main__":
    unittest.main()
