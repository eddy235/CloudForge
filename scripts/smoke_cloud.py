"""Check a fictional Render/App Runner demo and optionally save a JSON report.

Readiness retries tolerate Free-plan cold starts. Security failures are immediate.
No response bodies, header values or credentials are written to reports.
"""
import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

BODY_LIMIT = 150_000
TRANSIENT_STATUSES = {429, 502, 503, 504}
PRIVATE_PATHS = (
    "/admin/", "/login/", "/tickets/", "/tickets/new/",
    "/assets/", "/reports/", "/reports/export.csv",
)
WRITE_PATHS = ("/demo/", "/tickets/new/", "/reports/export.csv")


class VerificationError(AssertionError):
    """An explicit failure, including when Python is optimized with -O."""

    report = None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_origin(origin):
    if not isinstance(origin, str) or any(ord(c) <= 32 or ord(c) > 126 for c in origin):
        raise ValueError("Provide an ASCII HTTPS origin without whitespace")
    origin = origin.rstrip("/")
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Use a valid HTTPS origin (no HTTP)")
    if (parsed.path or parsed.query or parsed.fragment
            or parsed.username is not None or parsed.password is not None):
        raise ValueError("Provide only the HTTPS origin, without a path, query or credentials")
    if parsed.port not in (None, 443):
        raise ValueError("Only the standard HTTPS port is supported")
    if (not re.fullmatch(r"[a-z0-9.-]+", parsed.hostname)
            or not parsed.hostname.endswith((".onrender.com", ".awsapprunner.com"))):
        raise ValueError("Only a Render or AWS App Runner demo origin is supported")
    return origin


def probe(origin, path, method="GET"):
    request = Request(origin + path, method=method,
                      headers={"User-Agent": "CloudForge-Cloud-Smoke/0.3"})
    try:
        response = build_opener(NoRedirect()).open(request, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read(BODY_LIMIT + 1)
        if len(raw) > BODY_LIMIT:
            raise ValueError("Response exceeded the verification size limit")
        return response.code, response.headers, raw


def verify(origin, *, attempts=1, retry_delay=5):
    origin = validate_origin(origin)
    if not isinstance(attempts, int) or not 1 <= attempts <= 12:
        raise ValueError("Readiness attempts must be between 1 and 12")
    if not 0 <= retry_delay <= 30:
        raise ValueError("Readiness retry delay must be between 0 and 30 seconds")
    started = time.monotonic()
    revision = os.environ.get("GITHUB_SHA", "")
    report = {
        "schema_version": 1, "origin": origin, "status": "fail",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "checks": [], "readiness_attempts": [],
        # Checker revision, not an attestation of the running service's source.
        "verifier_revision": revision if re.fullmatch(r"[0-9a-f]{40}", revision) else None,
    }

    def require(condition, message):
        if not condition:
            raise VerificationError(message)

    def checked(path, method="GET", expected=200, inspect=None):
        item = {"path": path, "method": method, "status": None, "ok": False}
        report["checks"].append(item)
        before = time.monotonic()
        try:
            status, headers, raw = probe(origin, path, method)
            item["status"] = status
            require(status == expected,
                    f"{method} {path} returned HTTP {status}; expected {expected}")
            if inspect:
                inspect(headers, raw)
            item["ok"] = True
        except (URLError, OSError, ValueError) as error:
            raise VerificationError(f"{method} {path}: {type(error).__name__}") from error
        finally:
            item["elapsed_ms"] = round((time.monotonic() - before) * 1000)

    try:
        health = {"path": "/health/", "method": "GET", "status": None, "ok": False}
        report["checks"].append(health)
        for attempt in range(1, attempts + 1):
            entry = {"attempt": attempt, "status": None}
            report["readiness_attempts"].append(entry)
            try:
                status, _, raw = probe(origin, "/health/")
                entry["status"] = health["status"] = status
            except (URLError, OSError) as error:
                entry["error"] = type(error).__name__
                if attempt == attempts:
                    raise VerificationError("Health endpoint did not become reachable") from error
            else:
                if status not in TRANSIENT_STATUSES or attempt == attempts:
                    require(status == 200, f"Health endpoint returned HTTP {status}")
                    try:
                        data = json.loads(raw)
                    except (ValueError, UnicodeError) as error:
                        raise VerificationError("Health endpoint did not return valid JSON") from error
                    require(isinstance(data, dict) and data.get("demo_mode") is True,
                            "Cloud service is NOT in synthetic demo mode")
                    health["ok"] = True
                    break
            time.sleep(retry_delay)
        health["elapsed_ms"] = round((time.monotonic() - started) * 1000)

        def demo_content(headers, raw):
            try:
                html = raw.decode("utf-8")
            except UnicodeError as error:
                raise VerificationError("Demo did not return UTF-8 content") from error
            for marker in ("NexusDesk", "SYNTHETIC DATA ONLY", "Asset lifecycle"):
                require(marker in html, f"Demo missing expected marker: {marker}")
            directives = {}
            for directive in headers.get("Content-Security-Policy", "").split(";"):
                parts = directive.split()
                if parts:
                    require(parts[0] not in directives, "Duplicate Content Security Policy directive")
                    directives[parts[0]] = parts[1:]
            require(directives.get("script-src") == ["'none'"],
                    "Missing restrictive Content Security Policy")
            require(directives.get("frame-ancestors") == ["'none'"],
                    "Missing anti-framing Content Security Policy")
            require(headers.get("X-Content-Type-Options", "").lower() == "nosniff",
                    "Missing nosniff header")

        checked("/demo/", inspect=demo_content)
        checked("/static/desk/style.css")
        for path in PRIVATE_PATHS:
            checked(path, expected=404)
        # Empty write attempts are sent only after identifying the synthetic demo.
        for path in WRITE_PATHS:
            checked(path, method="POST", expected=404)
        report["status"] = "pass"
    except (VerificationError, ValueError) as error:
        failure = error if isinstance(error, VerificationError) else VerificationError(str(error))
        report["error"] = str(failure)
        failure.report = report
        raise failure from (error if failure is not error else None)
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_ms"] = round((time.monotonic() - started) * 1000)
        if report["checks"]:
            report["checks"][0].setdefault("elapsed_ms", report["elapsed_ms"])
        report["passed"] = sum(item["ok"] for item in report["checks"])
        report["total"] = len(report["checks"])
    return report


def save_results(report, path=None):
    if path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(f"## CloudForge deployment check: {report['status'].upper()}\n\n")
            stream.write("Checks the currently deployed demo; does not deploy code "
                         "or attest its source revision.\n\n")
            stream.write("| Request | HTTP | Result | Time (ms) |\n|---|---|---|---|\n")
            for item in report["checks"]:
                stream.write(f"| {item['method']} {item['path']} | {item['status']} | "
                             f"{'pass' if item['ok'] else 'FAIL'} | "
                             f"{item.get('elapsed_ms', '—')} |\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origin", help="HTTPS origin of a fictional Render/App Runner demo")
    parser.add_argument("--attempts", type=int, default=8, help="Readiness attempts (1–12)")
    parser.add_argument("--retry-delay", type=float, default=5, help="Readiness retry delay in seconds")
    parser.add_argument("--report", help="Optional JSON report path")
    args = parser.parse_args(argv)
    try:
        report = verify(args.origin, attempts=args.attempts, retry_delay=args.retry_delay)
    except (VerificationError, ValueError) as error:
        report = getattr(error, "report", None) or {
            "schema_version": 1, "status": "fail", "origin": None,
            "checks": [], "error": str(error), "passed": 0, "total": 0,
        }
        save_results(report, args.report)
        print(f"FAIL: {error}")
        return 1
    save_results(report, args.report)
    print(f"PASS: {report['passed']}/{report['total']} HTTPS demo, assets, headers and isolation checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
