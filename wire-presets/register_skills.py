#!/usr/bin/env python3
"""Register wire-analysis-presets skills into the MCP Gateway (mcp.finddatatech.cloud).

Idempotent: reads the existing skill list first and only registers the diff
(by name). Token is read from ~/.config/finddata/gateway-token.json (never
from this repo). Re-login via the gateway UI when the access token expires
(the 配方 is in references/gateway-token.md; SSO session survives for days).

Usage:
  python3 docs/wire-presets/register_skills.py            # register missing skills
  python3 docs/wire-presets/register_skills.py --rescan   # also run security-scan
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error

GATEWAY = "https://mcp.finddatatech.cloud"
# 技能源托管：Gitee `finddata-skills` 仓的 wire-presets/ 目录。
# 为什么走 Gitee 而不是 GitHub：registry 容器抓不到 raw.githubusercontent.com
# （2026-10-12 实测：GitHub raw 本机 200、registry 注册报 "Invalid SKILL.md URL: "
# 空串——即容器内抓取失败）；而网关已注册的 20 个技能全部是 Gitee raw URL，
# 说明 Gitee 是 registry 侧验证可达的通道。Gitee raw 返回 302，registry 会跟随。
RAW_BASE = "https://gitee.com/FindDataTechnology/finddata-skills/raw/master/wire-presets"
REPO_URL = "https://gitee.com/FindDataTechnology/finddata-skills/tree/master/wire-presets"
TOKEN_PATH = os.path.expanduser("~/.config/finddata/gateway-token.json")

# 两层都要可见：wire-customers（柏讯客户层）+ analysts（壹座数据线层）。
# 组名与 Logto 组织 auto-ID 都列（平台 groups claim 两种形态都出现过）。
ALLOWED_GROUPS = ["wire-customers", "tdwwx4not5ck", "analysts", "sl63fy08ruh9"]

SKILLS = [
    ("macro-cycle-analysis", ["wire", "经济", "宏观", "finddata"]),
    ("industry-chain-analysis", ["wire", "经济", "行业", "finddata"]),
    ("regional-economy-compare", ["wire", "经济", "区域", "finddata"]),
    ("corporate-fundamental-analysis", ["wire", "金融", "公司", "finddata"]),
    ("panel-econometrics", ["wire", "经济", "计量", "finddata"]),
    ("statistical-inference", ["wire", "经济", "统计", "finddata"]),
    ("equity-valuation", ["wire", "金融", "估值", "finddata"]),
    ("earnings-cycle-analysis", ["wire", "金融", "财报", "finddata"]),
    # 批 2 首批 pack 的技能（2026-10-17）
    ("equity-research-data", ["wire", "投研", "取数", "finddata"]),
    ("equity-research-peers", ["wire", "投研", "同业", "finddata"]),
    ("equity-research-modeling", ["wire", "投研", "建模", "finddata"]),
    ("equity-research-thesis", ["wire", "投研", "论点", "finddata"]),
    ("equity-research-report", ["wire", "投研", "报告", "finddata"]),
    ("decision-review-log", ["wire", "复盘", "账本", "finddata"]),
    ("decision-review-settlement", ["wire", "复盘", "结算", "finddata"]),
    ("decision-review-reflection", ["wire", "复盘", "反思", "finddata"]),
    ("decision-review-portfolio", ["wire", "复盘", "持仓", "finddata"]),
    # 批 3：农业垂直线（申万农林牧渔）两个包（2026-11-08，change
    # add-agriculture-industry-sources W3 6.1/6.2）。价格侧只走本地观测库通道，
    # 服务端数据面只用于非价格序列（W3 6.3）。
    ("agri-industry-watch", ["wire", "农业", "景气", "finddata"]),
    ("agri-cost-chain", ["wire", "农业", "成本", "finddata"]),
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


def load_description(skill_dir: str, name: str) -> str:
    """Parse frontmatter description from the local SKILL.md."""
    here = os.path.dirname(os.path.abspath(__file__))
    # 仓内布局：wire-presets/<name>/SKILL.md（本脚本与技能目录同级）。
    # docs/wire-presets 源版是 skills/<name>/SKILL.md，多一层，勿照抄。
    path = os.path.join(here, name, "SKILL.md")
    txt = open(path, encoding="utf-8").read()
    parts = txt.split("---", 2)
    fm: dict[str, str] = {}
    for line in parts[1].splitlines():
        k, _, v = line.partition(":")
        if k.strip() in ("name", "description", "version"):
            fm[k.strip()] = v.strip().strip('"')
    desc = fm.get("description") or f"{name} skill (wire-analysis-presets)"
    return desc if len(desc) <= 1000 else desc[:997] + "..."


def main() -> int:
    if not os.path.exists(TOKEN_PATH):
        print(f"FATAL: gateway token not found at {TOKEN_PATH}")
        print("  Log in at https://mcp.finddatatech.cloud and copy the JWT"
              " (右上 Get JWT Token) into that file as"
              ' {"tokens": {"access_token": "..."}}.')
        return 1
    token = json.load(open(TOKEN_PATH))["tokens"]["access_token"]

    def all_skills() -> tuple[set[str], list[dict]]:
        """分页取全量技能名与整条目。

        **必须翻页**：`GET /api/skills` 默认只回 20 条（2026-10-17 实测
        `total_count=212`、`limit=20`）。只读第一页会让"已注册"被误判成"缺失"
        ——首次跑就踩到：8 个既有技能被当新技能重提交（返回 409），而末段
        verification 报 `0/17 registered`，与事实相反。

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
    for name, tags in SKILLS:
        if name in known:
            print(f"SKIP  {name} (already registered)")
            continue
        desc = load_description(name, name)
        payload = {
            "name": name,
            "description": desc,
            "skill_md_url": f"{RAW_BASE}/{name}/SKILL.md",
            "repository_url": f"{REPO_URL}/tree/main/skills/{name}",
            "license": "See ATTRIBUTION block in the skill file",
            "tags": tags,
            "visibility": "public",
            "status": "active",
            "allowed_groups": ALLOWED_GROUPS,
        }
        st, body = api("POST", "/api/skills", token, payload)
        ok = st in (200, 201)
        print(f"{'OK  ' if ok else 'FAIL'} {name} -> {st} {str(body)[:160]}")
        results.append({"name": name, "status": st,
                        "path": (body or {}).get("path") if isinstance(body, dict) else None})

    after_names, after_items = all_skills()
    missing = [n for n, _ in SKILLS if n not in after_names]
    print(f"\nverification: {len(SKILLS) - len(missing)}/{len(SKILLS)} registered;"
          f" missing={missing or 'none'}")

    if "--rescan" in sys.argv:
        for s in after_items:
            if s.get("name") not in {n for n, _ in SKILLS}:
                continue
            leaf = s.get("path", "").rstrip("/").rsplit("/", 1)[-1]
            st2, body2 = api("POST", f"/api/skills/{leaf}/security-scan", token, {})
            print(f"scan {leaf}: {st2} {str(body2)[:120]}")
    return 0 if not missing else 2


if __name__ == "__main__":
    sys.exit(main())
