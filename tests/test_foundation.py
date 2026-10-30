"""Offline checks that are independent of Docker, Terraform and AWS credentials."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT/path).read_text(encoding='utf-8')


class FoundationTests(unittest.TestCase):
    def test_application_dependency_pinned_in_workflows(self):
        ref = re.search(r'^COMMIT=([0-9a-f]{40})$', read('UPSTREAM_VERSION'), re.M)
        self.assertIsNotNone(ref)
        self.assertIn('eddy235/NexusDesk', read('UPSTREAM_VERSION'))
        for file in ('.github/workflows/ci.yml', '.github/workflows/ecr-publish.yml'):
            self.assertIn('ref: '+ref.group(1), read(file))
            self.assertIn('persist-credentials: false', read(file))

    def test_public_demo_is_immutable_and_local_compose_isolation(self):
        dockerfile = read('Dockerfile')
        compose = read('compose.yaml')
        self.assertIn('USER app', dockerfile)
        self.assertIn('HEALTHCHECK', dockerfile)
        self.assertIn('NEXUSDESK_DEMO_MODE: "true"', compose)
        self.assertIn('DJANGO_DEBUG: "false"', compose)
        self.assertIn('127.0.0.1:8000:8000', compose)
        self.assertIn('read_only: true', compose)
        self.assertIn('no-new-privileges:true', compose)
        self.assertIn('cap_drop:', compose)
        for forbidden in ('AWS_ACCESS_KEY_ID=', 'AWS_SECRET_ACCESS_KEY='):
            self.assertNotIn(forbidden, compose)

    def test_terraform_creates_registry_not_billable_compute(self):
        tf = read('infra/terraform/main.tf')
        self.assertIn('resource "aws_ecr_repository"', tf)
        self.assertIn('image_tag_mutability = "IMMUTABLE"', tf)
        self.assertIn('scan_on_push = true', tf)
        self.assertIn('encryption_type = "AES256"', tf)
        self.assertNotRegex(tf, r'resource\s+"aws_(?:instance|ecs_service|nat_gateway|lb|apprunner_service)"')
        self.assertIn('token.actions.githubusercontent.com:sub', tf)
        self.assertIn('repo:${var.github_repository}:ref:refs/heads/main', tf)
        self.assertIn('sts.amazonaws.com', tf)
        self.assertIn('resources = [aws_ecr_repository.nexusdesk.arn]', tf)
        self.assertIn('github_oidc_provider_arn == "" ? 0 : 1', tf)

    def test_aws_publish_is_opt_in_without_keys(self):
        ci = read('.github/workflows/ci.yml')
        publish = read('.github/workflows/ecr-publish.yml')
        self.assertNotIn('configure-aws-credentials', ci)
        self.assertNotIn('terraform apply', ci)
        self.assertIn('workflow_dispatch:', publish)
        self.assertNotRegex(publish, r'(?m)^\s+push:')
        self.assertIn("github.ref == 'refs/heads/main'", publish)
        self.assertIn('id-token: write', publish)
        self.assertIn('vars.AWS_ROLE_ARN', publish)
        self.assertIn('vars.ECR_REPOSITORY_URI', publish)
        self.assertIn('aws-actions/configure-aws-credentials', publish)
        self.assertNotIn('AWS_SECRET_ACCESS_KEY', publish)

    def test_sensitive_files_are_ignored(self):
        ignore = read('.gitignore')
        for item in ('*.tfstate', '.env', 'upstream/NexusDesk/', '*.pem'):
            self.assertIn(item, ignore)


if __name__ == '__main__':
    unittest.main()
