#!/usr/bin/env python3
"""Smoke test all API endpoints."""
import subprocess, json, sys

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbi11c2VyIiwidGVuYW50X2lkIjoiZGVmYXVsdCIsInJvbGUiOiJhZG1pbiIsInR2IjowLCJleHAiOjE3ODAzNjQ3MzAsImp0aSI6IjI4ZTYwMmE3LWZmODAtNDM3NS05YWNjLTMwZjQwNGE5YzRlYyJ9.kT33KQWPsCnCG5K0V-wXaXNtdu9MIynDvWQEboO5ivs"
BASE = "http://localhost:8000/api/v1"

def curl(method, path, data=None):
    cmd = ["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code}", "-H", f"Authorization: Bearer {TOKEN}"]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    cmd += ["-X", method, f"{BASE}{path}"]
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

endpoints = [
    ("GET", "/auth/me", None, "200"),
    ("GET", "/agents?page=1&size=1", None, "200"),
    ("POST", "/agents", {"name":"test","description":""}, "201"),
    ("GET", "/knowledge/bases?page=1&size=1", None, "200"),
    ("POST", "/knowledge/bases", {"name":"test"}, "201"),
    ("GET", "/conversations?page=1&size=1", None, "200"),
    ("GET", "/models/providers", None, "200"),
    ("GET", "/models/configs", None, "200"),
    ("GET", "/workflows?page=1&size=1", None, "200"),
    ("GET", "/tools?page=1&size=1", None, "200"),
    ("GET", "/tools/builtin", None, "200"),
    ("GET", "/users?page=1&size=1", None, "200"),
    ("GET", "/tenants?page=1&size=1", None, "200"),
    ("GET", "/audit?page=1&size=1", None, "200"),
    ("GET", "/marketplace/items?page=1&size=1", None, "200"),
    ("GET", "/marketplace/categories", None, "200"),
    ("GET", "/tokens", None, "200"),
    ("GET", "/roles", None, "200"),
    ("GET", "/usage/daily?page=1&size=1", None, "200"),
    ("GET", "/usage/models?page=1&size=1", None, "200"),
    ("GET", "/evaluations?page=1&size=1", None, "200"),
    ("GET", "/multi-agent/crews?page=1&size=1", None, "200"),
    ("GET", "/triggers?page=1&size=1", None, "200"),
    ("GET", "/webhooks?page=1&size=1", None, "200"),
    ("GET", "/variables?page=1&size=1", None, "200"),
    ("GET", "/publish/channels", None, "200"),
    ("GET", "/import/platforms", None, "200"),
    ("GET", "/import/tasks?page=1&size=1", None, "200"),
    ("GET", "/plugins?page=1&size=1", None, "200"),
    ("GET", "/compliance/score", None, "200"),
    ("GET", "/models/compare/supported", None, "200"),
    ("GET", "/chat/completions", None, "200"),
    ("GET", "/memory/context/test", None, "200"),
    ("GET", "/tasks/status/test", None, "404"),
]

failures = []
for method, path, data, expect in endpoints:
    code = curl(method, path, data)
    ok = code == expect or (expect == "200" and code == "307")
    status = "OK" if ok else "FAIL"
    if not ok:
        failures.append(f"{method} {path}: {code} (expected {expect})")
    print(f"{status}: {method} {path} -> {code}")

if failures:
    print(f"\n{len(failures)} FAILURES:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
else:
    print("\nAll endpoints passed smoke test.")
