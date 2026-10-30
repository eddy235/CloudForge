"""AWS-free Render deployment safety and dependency tests."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class RenderDeploymentTests(unittest.TestCase):
    def test_upstream_is_exactly_the_reviewed_public_commit(self):
        commit = re.search(r"^COMMIT=([0-9a-f]{40})$", read("UPSTREAM_VERSION"), re.M)
        self.assertIsNotNone(commit)
        docker = read("Dockerfile.render")
        self.assertIn(f"ARG NEXUSDESK_COMMIT={commit.group(1)}", docker)
        self.assertIn('test "$(git rev-parse HEAD)" = "${NEXUSDESK_COMMIT}"', docker)
        self.assertIn("rm -rf .git", docker)
        self.assertIn("USER app", docker)
        self.assertIn("HEALTHCHECK", docker)
        self.assertNotIn("AWS_ACCESS_KEY_ID", docker)

    def test_blueprint_protects_public_demo_and_uses_free_plan(self):
        blueprint = read("render.yaml")
        for expected in (
            "name: cloudforge-demo",
            "runtime: docker",
            "plan: free",
            "repo: https://github.com/eddy235/CloudForge",
            "branch: main",
            "dockerfilePath: ./Dockerfile.render",
            "autoDeployTrigger: checksPass",
            "healthCheckPath: /health/",
            "generateValue: true",
            'value: ".onrender.com,localhost,127.0.0.1"',
        ):
            self.assertIn(expected, blueprint)
        for name, setting in (
            ("NEXUSDESK_DEMO_MODE", "true"),
            ("DJANGO_DEBUG", "false"),
            ("DJANGO_ENABLE_HSTS", "true"),
        ):
            self.assertRegex(
                blueprint,
                r"- key: " + name + r"\n\s+value: \"" + setting + r"\"",
            )
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", blueprint)
        self.assertNotIn("DATABASE_URL", blueprint)

    def test_render_build_is_checked_by_ci_without_cloud_credentials(self):
        workflow = read(".github/workflows/ci.yml")
        self.assertIn("docker build -f Dockerfile.render", workflow)
        self.assertIn("scripts/smoke_local.py", workflow)
        self.assertNotIn("terraform apply", workflow)
        self.assertNotIn("aws-actions/configure-aws-credentials", workflow)


if __name__ == "__main__":
    unittest.main()
