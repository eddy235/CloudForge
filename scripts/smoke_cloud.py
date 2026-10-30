"""Read-only HTTPS verification for an explicitly deployed AWS App Runner demo.

Usage:
  python scripts/smoke_cloud.py https://your-service.region.awsapprunner.com

Do not pass an operational helpdesk URL: the probe intentionally checks for a
synthetic public demonstration and that every internal route is inaccessible.
"""
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def probe(origin, path, method="GET"):
    request = Request(
        origin + path,
        method=method,
        headers={"User-Agent": "CloudForge-Cloud-Smoke/0.2"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            return response.status, response.headers, response.read(150000)
    except HTTPError as error:
        return error.code, error.headers, error.read(150000)


def verify(origin):
    origin = origin.rstrip("/")
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Use a valid HTTPS origin (no HTTP)")
    if parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Provide only the HTTPS origin, without a path, query or credentials")

    status, headers, raw = probe(origin, "/health/")
    assert status == 200, f"Health endpoint returned HTTP {status}"
    health = json.loads(raw)
    assert health.get("demo_mode") is True, "Cloud service is NOT in synthetic demo mode"

    status, headers, raw = probe(origin, "/demo/")
    assert status == 200, f"Fictional demo returned HTTP {status}"
    html = raw.decode("utf-8")
    for marker in ("NexusDesk", "SYNTHETIC DATA ONLY", "Asset lifecycle"):
        assert marker in html, f"Demo missing expected marker: {marker}"
    csp = headers.get("Content-Security-Policy", "")
    assert "script-src 'none'" in csp, "Missing restrictive Content Security Policy"
    assert "frame-ancestors 'none'" in csp, "Missing anti-framing Content Security Policy"
    assert headers.get("X-Content-Type-Options", "").lower() == "nosniff", "Missing nosniff header"

    status, _, _ = probe(origin, "/static/desk/style.css")
    assert status == 200, f"Demo static CSS returned HTTP {status}"
    for path in ("/admin/", "/login/", "/tickets/", "/tickets/new/",
                 "/assets/", "/reports/", "/reports/export.csv"):
        status, _, _ = probe(origin, path)
        assert status == 404, f"Internal route {path} returned HTTP {status}; expected 404"
    for path in ("/demo/", "/tickets/new/", "/reports/export.csv"):
        status, _, _ = probe(origin, path, "POST")
        assert status == 404, f"Write attempt {path} returned HTTP {status}; expected 404"
    print("PASS: CloudForge v0.2 HTTPS synthetic demo, assets, headers and private-route isolation")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/smoke_cloud.py https://service.awsapprunner.com")
    try:
        verify(sys.argv[1])
    except (AssertionError, ValueError, URLError, json.JSONDecodeError) as error:
        raise SystemExit(f"FAIL: {error}") from error
