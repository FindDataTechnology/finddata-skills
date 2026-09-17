#!/usr/bin/env python3
"""Register finddata-skills into the MCP Gateway (mcp.finddatatech.cloud).

Idempotent: reads the existing skill list first and only registers the diff
(by name). Token is read from ~/.config/finddata/gateway-token.json (never
from this repo). Re-login via the gateway UI when the 8h access token
expires (no refresh token is issued).

Usage:
  python3 scripts/register_skills.py            # register missing skills
  python3 scripts/register_skills.py --rescan   # also run security-scan on all
"""
import json
import os
import sys
import urllib.request
import urllib.error

GATEWAY = "https://mcp.finddatatech.cloud"
GITEE_RAW = "https://gitee.com/FindDataTechnology/finddata-skills/raw/master"
REPO_URL = "https://gitee.com/FindDataTechnology/finddata-skills"
TOKEN_PATH = os.path.expanduser("~/.config/finddata/gateway-token.json")

# (category_dir, skill_name, tags, version)
SKILLS = [
    ("research-methods", "earnings-analysis", ["finance", "research-methods", "finddata", "anthropics"], None),
    ("research-methods", "sector-overview", ["finance", "research-methods", "finddata", "anthropics"], None),
    ("research-methods", "comps-analysis", ["finance", "research-methods", "finddata", "anthropics"], None),
    ("research-methods", "dcf-model", ["finance", "research-methods", "finddata", "anthropics"], None),
    ("research-methods", "3-statement-model", ["finance", "research-methods", "finddata", "anthropics"], None),
    ("research-methods", "returns-analysis", ["finance", "research-methods", "finddata", "anthropics"], None),
    ("research-methods", "ic-memo", ["finance", "research-methods", "finddata", "anthropics"], None),
    ("research-methods", "macro-rates-monitor", ["finance", "research-methods", "finddata", "anthropics", "lseg"], None),
    ("market-analysis", "company-valuation", ["finance", "market-analysis", "finddata", "himself65"], None),
    ("market-analysis", "stock-correlation", ["finance", "market-analysis", "finddata", "himself65"], None),
    ("market-analysis", "earnings-preview", ["finance", "market-analysis", "finddata", "himself65"], None),
    ("market-analysis", "earnings-recap", ["finance", "market-analysis", "finddata", "himself65"], None),
    ("cn-market", "akshare-stock", ["finance", "cn-market", "a-share", "finddata", "molezzz"], None),
    ("us-market", "stock-analysis", ["finance", "us-market", "finddata", "claude-office-skills"], "1.0.0"),
    ("sentiment", "last30days", ["sentiment", "research", "finddata", "mvanhorn"], "3.24.0"),
    ("data-analysis", "data-analysis", ["data-analysis", "spreadsheet", "finddata", "claude-office-skills"], "1.0.0"),
    ("data-analysis", "exploratory-data-analysis", ["data-analysis", "eda", "finddata", "k-dense"], None),
    ("data-analysis", "statsmodels", ["data-analysis", "econometrics", "finddata", "k-dense"], None),
    ("data-analysis", "statistical-analysis", ["data-analysis", "statistics", "finddata", "k-dense"], None),
]


def api(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, object]:
    req = urllib.request.Request(GATEWAY + path, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data, timeout=30) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:300]


def load_description(category: str, name: str) -> tuple[str, str | None]:
    """Parse frontmatter from the sibling SKILL.md; return (description, version)."""
    path = os.path.join(os.path.dirname(__file__), "..", category, name, "SKILL.md")
    txt = open(path, encoding="utf-8").read()
    parts = txt.split("---", 2)
    fm = {}
    for line in parts[1].splitlines():
        if line.startswith("name:") or line.startswith("version:"):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"')
        elif line.startswith("description:"):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"')
    desc = fm.get("description") or f"{name} skill from finddata-skills ({category})"
    if len(desc) > 1000:
        desc = desc[:997] + "..."
    return desc, fm.get("version")


def main() -> int:
    token = json.load(open(TOKEN_PATH))["tokens"]["access_token"]
    status, existing = api("GET", "/api/skills", token)
    if status != 200:
        print(f"FATAL: GET /api/skills -> {status}: {existing}")
        return 1
    items = existing if isinstance(existing, list) else existing.get("skills", [])
    known = {s.get("name") for s in items}
    print(f"existing skills on gateway: {len(known)} -> {sorted(known)}")

    results = []
    for category, name, tags, version in SKILLS:
        if name in known:
            print(f"SKIP  {name} (already registered)")
            continue
        desc, fmver = load_description(category, name)
        payload = {
            "name": name,
            "description": desc,
            "skill_md_url": f"{GITEE_RAW}/{category}/{name}/SKILL.md",
            "repository_url": f"{REPO_URL}/tree/master/{category}/{name}",
            "version": version or fmver,
            "license": "See ATTRIBUTION.md in the skill directory",
            "tags": tags,
            "visibility": "public",
            "status": "active",
        }
        st, body = api("POST", "/api/skills", token, payload)
        print(f"{'OK ' if st in (200, 201) else 'FAIL'} {name} -> {st} {(str(body)[:160])}")
        results.append({"name": name, "status_code": st, "path": (body or {}).get("path") if isinstance(body, dict) else None})

    # verify
    st, after = api("GET", "/api/skills", token)
    after_items = after if isinstance(after, list) else after.get("skills", [])
    after_names = {s.get("name") for s in after_items}
    missing = [n for _, n, _, _ in SKILLS if n not in after_names]
    print(f"\nverification: {len(SKILLS) - len(missing)}/{len(SKILLS)} registered; missing={missing or 'none'}")

    if "--rescan" in sys.argv:
        for s in after_items:
            if s.get("name") not in {n for _, n, _, _ in SKILLS}:
                continue
            leaf = s.get("path", "").rstrip("/").rsplit("/", 1)[-1]
            st, body = api("POST", f"/api/skills/{leaf}/security-scan", token, {})
            print(f"scan {leaf}: {st} {str(body)[:120]}")
    return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())
