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

    def all_skills() -> tuple[set[str], list[dict]]:
        """分页取全量（names, items）。

        **必须翻页**：`GET /api/skills` 默认只回 20 条（2026-10-17 实测
        `total_count=212`、`limit=20`）。只读第一页会把"已注册"误判成"缺失"，
        触发对既有技能的重提交，而 verification 又用同一份残缺列表，
        报出与事实相反的结果。

        返回 (names, items)：names 供判重/verification，items 供 --rescan
        拼 security-scan URL（该分支要 s["path"]，光有名字集不够）。
        """
        names: set[str] = set()
        items: list[dict] = []
        offset = 0
        while True:
            st, page = api("GET", f"/api/skills?limit=100&offset={offset}", token)
            if st != 200:
                raise RuntimeError(f"GET /api/skills -> {st}: {page}")
            rows = page if isinstance(page, list) else (page.get("skills") or [])
            items.extend(rows)
            names.update(s.get("name") for s in rows if s.get("name"))
            if isinstance(page, dict) and page.get("has_next") and rows:
                offset += len(rows)
                continue
            break
        return names, items

    try:
        known, _ = all_skills()
    except RuntimeError as exc:
        print(f"FATAL: {exc}")
        return 1
    print(f"existing skills on gateway: {len(known)}")

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
    after_names, after_items = all_skills()
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
