"""Operational failure cases; all requests and readiness delays are simulated."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from scripts.smoke_cloud import VerificationError, main, save_results, verify

ORIGIN = "https://cloudforge-demo.onrender.com"
HEADERS = {
    "Content-Security-Policy": "default-src 'none'; script-src 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
}


def demo_probe(origin, path, method="GET"):
    if method == "POST":
        return 404, {}, b"blocked"
    if path == "/health/":
        return 200, {}, b'{"demo_mode":true}'
    if path == "/demo/":
        return 200, HEADERS, b"NexusDesk SYNTHETIC DATA ONLY Asset lifecycle"
    if path == "/static/desk/style.css":
        return 200, {}, b"body {}"
    return 404, {}, b"blocked"


class OperationalChecksTests(unittest.TestCase):
    def test_untrusted_targets_are_rejected_before_network_access(self):
        targets = (
            "https://127.0.0.1", "https://169.254.169.254", "https://example.com",
            "https://cloudforge-demo.onrender.com.evil.com",
            "https://user:secret@cloudforge-demo.onrender.com",
            "https://@cloudforge-demo.onrender.com", ORIGIN + ":8443",
            ORIGIN + "/demo/", ORIGIN + "?secret=hidden", ORIGIN + "#fragment",
            ORIGIN + "\n", " https://cloudforge-demo.onrender.com",
        )
        with patch("scripts.smoke_cloud.probe") as probe:
            for origin in targets:
                with self.subTest(origin=origin), self.assertRaises(ValueError):
                    verify(origin)
            probe.assert_not_called()

    def test_success_report_has_thirteen_checks_without_response_data(self):
        with patch("scripts.smoke_cloud.probe", side_effect=demo_probe):
            report = verify(ORIGIN + "/")
        self.assertEqual((report["status"], report["passed"], report["total"]), ("pass", 13, 13))
        self.assertTrue(all(c["ok"] and c["elapsed_ms"] >= 0 for c in report["checks"]))
        self.assertNotIn("SYNTHETIC DATA ONLY", json.dumps(report))
        self.assertNotIn("Content-Security-Policy", json.dumps(report))

    def test_transient_cold_start_and_timeout_are_retried_only_for_health(self):
        health = iter([(503, {}, b"starting"), URLError("private diagnostic"),
                       (200, {}, b'{"demo_mode":true}')])

        def cold_probe(origin, path, method="GET"):
            if path == "/health/":
                item = next(health)
                if isinstance(item, Exception):
                    raise item
                return item
            return demo_probe(origin, path, method)

        with patch("scripts.smoke_cloud.probe", side_effect=cold_probe), \
                patch("scripts.smoke_cloud.time.sleep") as sleep:
            report = verify(ORIGIN, attempts=3)
        self.assertEqual(len(report["readiness_attempts"]), 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertNotIn("private diagnostic", json.dumps(report))

    def test_permanent_health_failure_does_not_retry_or_probe_any_other_route(self):
        with patch("scripts.smoke_cloud.probe", return_value=(404, {}, b"no")) as probe, \
                patch("scripts.smoke_cloud.time.sleep") as sleep:
            with self.assertRaises(VerificationError) as failure:
                verify(ORIGIN, attempts=5)
        self.assertEqual(probe.call_count, 1)
        sleep.assert_not_called()
        self.assertEqual(failure.exception.report["status"], "fail")

    def test_unready_service_stops_after_the_attempt_limit(self):
        with patch("scripts.smoke_cloud.probe", return_value=(503, {}, b"starting")) as probe, \
                patch("scripts.smoke_cloud.time.sleep"):
            with self.assertRaises(VerificationError) as failure:
                verify(ORIGIN, attempts=3)
        self.assertEqual(probe.call_count, 3)
        self.assertEqual(failure.exception.report["passed"], 0)

    def test_operational_or_malformed_health_never_reaches_write_probes(self):
        for raw in (b'{"demo_mode":false}', b'{"demo_mode":"true"}', b"[]", b"not-json"):
            with self.subTest(raw=raw), \
                    patch("scripts.smoke_cloud.probe", return_value=(200, {}, raw)) as probe:
                with self.assertRaises(VerificationError):
                    verify(ORIGIN, attempts=3)
                self.assertEqual(probe.call_count, 1)

    def test_unsafe_csp_is_rejected_before_internal_or_write_probes(self):
        for csp in ("script-src 'none' https://evil.example; frame-ancestors 'none'",
                    "script-src 'none'; script-src *; frame-ancestors 'none'",
                    "script-src 'none'; frame-ancestors *"):
            def weak_probe(origin, path, method="GET"):
                if path == "/demo/":
                    return 200, {**HEADERS, "Content-Security-Policy": csp}, \
                        b"NexusDesk SYNTHETIC DATA ONLY Asset lifecycle"
                return demo_probe(origin, path, method)

            with self.subTest(csp=csp), patch("scripts.smoke_cloud.probe", side_effect=weak_probe) as probe:
                with self.assertRaises(VerificationError):
                    verify(ORIGIN)
                self.assertEqual(probe.call_count, 2)

    def test_exposed_private_route_fails_with_partial_evidence(self):
        def exposed_probe(origin, path, method="GET"):
            if path == "/admin/":
                return 200, {}, b"secret response not for reports"
            return demo_probe(origin, path, method)

        with patch("scripts.smoke_cloud.probe", side_effect=exposed_probe) as probe:
            with self.assertRaises(VerificationError) as failure:
                verify(ORIGIN)
        report = failure.exception.report
        self.assertEqual(report["checks"][-1]["path"], "/admin/")
        self.assertFalse(report["checks"][-1]["ok"])
        self.assertNotIn("secret response", json.dumps(report))
        self.assertTrue(all(call.args[2:] != ("POST",) for call in probe.call_args_list))

    def test_redirects_and_allowed_write_attempts_fail_without_retry(self):
        for status, method, path in ((302, "GET", "/demo/"), (200, "POST", "/demo/")):
            def bad_probe(origin, actual_path, actual_method="GET"):
                if (actual_path, actual_method) == (path, method):
                    return status, {}, b"unexpected response"
                return demo_probe(origin, actual_path, actual_method)

            with self.subTest(status=status), patch("scripts.smoke_cloud.probe", side_effect=bad_probe), \
                    patch("scripts.smoke_cloud.time.sleep") as sleep:
                with self.assertRaises(VerificationError):
                    verify(ORIGIN, attempts=3)
                sleep.assert_not_called()

    def test_invalid_cli_target_still_writes_failure_report_without_the_secret(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            output = Path(tmp) / "check.json"
            with patch("builtins.print"):
                code = main(["https://user:private-secret@cloudforge-demo.onrender.com", "--report", str(output)])
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output.read_text())["status"], "fail")
            self.assertNotIn("private-secret", output.read_text())

    def test_json_and_github_summary_are_written_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            output, summary = Path(tmp) / "result.json", Path(tmp) / "summary.md"
            with patch("scripts.smoke_cloud.probe", side_effect=demo_probe):
                report = verify(ORIGIN)
            report["status"] = "fail"
            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}):
                save_results(report, output)
            self.assertEqual(json.loads(output.read_text())["status"], "fail")
            self.assertIn("FAIL", summary.read_text())
            self.assertIn("does not deploy code", summary.read_text())


if __name__ == "__main__":
    unittest.main()
