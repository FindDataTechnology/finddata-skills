#!/usr/bin/env python3
"""从技能稿组装柏讯套件快照（fleet-packs/wire-suites-snapshot/*.json）。

为什么要有生成器
----------------
套件快照把每个技能的正文**内联**进 JSON。手抄一份等于制造两份真源，改一处漂一处
（本仓已有过 `manifest 声明版本与资产实际版本漂移` 的先例）。因此一律由 SKILL.md
生成快照，不手改快照。

用法
----
    python finddata-skills/scripts/build_wire_suite.py macros

    # 或显式指定
    python finddata-skills/scripts/build_wire_suite.py \
        --suite-id wire-macro-analysis \
        --name "柏讯 · 宏观分析套件" \
        --entry macro-brief \
        --skills macro-brief macro-data-vintage macro-regime macro-transmission macro-scenario
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PRESET_ROOT = REPO / "finddata-skills" / "wire-presets"
OUT_ROOT = REPO / "fleet-packs" / "wire-suites-snapshot"

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)

SUITES = {
    "macros": {
        "suite_id": "wire-macro-analysis",
        "name": "柏讯 · 宏观分析套件",
        "description": (
            "宏观经济分析：带 vintage 纪律的取数、周期判定、宏观到行业的传导验证、"
            "条件-响应情景矩阵与口径表装配。每个序列必带来源/期别/取数时点/修订次数/"
            "回放等级五项，缺一项不进分析；回放等级非 exact 时不计算增长率。"
            "传导只报历史统计关系、不报因果；情景不给点值、概率与时间点。"
        ),
        "tags": ["wire", "宏观", "经济"],
        "entry_skill": "macro-brief",
        "skills": [
            "macro-brief",
            "macro-data-vintage",
            "macro-regime",
            "macro-transmission",
            "macro-scenario",
        ],
        "mcp_servers": [
            # 工具名以各 server 的 tool-surface.json 实测为准（wire-analysis-presets 第一闸）。
            {"registryName": "fd-open-data-mcp", "requiredGroup": "wire-customers",
             "allowTools": ["ai_search", "read", "read_series", "resolve_entity",
                            "get_entity", "list_concepts", "data_stats",
                            "coverage_report"]},
            {"registryName": "fd-find-data-business-mcp", "requiredGroup": "wire-customers",
             "allowTools": ["yearbook_read", "yearbook_regions",
                            "wb_read", "wb_search_indicators",
                            "gta_search_variables"]},
            {"registryName": "fd-quant", "requiredGroup": "wire-customers",
             "allowTools": ["detect_regime_slow", "document_regime_defaults",
                            "check_series_as_of_bounds", "validate_no_lookahead",
                            "check_observation_sufficiency", "summarize_beta",
                            "compute_sensitivity_grid"]},
        ],
        "persona": (
            "柏讯宏观分析助手：把宏观问题拆成取数、周期、传导、情景四段，最后装配成一张"
            "可逐格复核的口径表。每个序列必带来源、期别、取数时点、修订次数与回放等级；"
            "回放等级非 exact 时不计算任何增长率，也不把当前值当成当年值。传导只报历史"
            "统计关系，计算面无相关性工具时标「未验证（计算面缺相关性工具）」而不是手算。"
            "情景只给条件-响应，不给点值、概率与时间点。不预测、不给买卖建议。"
        ),
        "data_caliber": {
            "vintage": (
                "序列取数走 read_series 的 as_of_vintage；回放等级四态 "
                "exact / batch_unreplayable / vintage_unavailable / absent 逐点返回。"
                "任一点非 exact 时禁止计算同比环比（change: make-observation-vintage-readable）"
            ),
            "regime": "detect_regime_slow 产出判定；窗口、参数、阈值来源逐次重述",
            "transmission": (
                "计算面当前无相关系数 / 领先滞后工具 → 该类环节标注"
                "「未验证（计算面缺相关性工具）」，禁止手算"
            ),
            "scenario": "条件-响应矩阵；敏感度优先 compute_sensitivity_grid，无来源的区间不出现",
            "brief": "口径表七列强制（指标/来源/期别/最新期/修订次数/回放等级/缺口说明）+ 总可回放性声明",
        },
    },
}


def parse_skill(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER.match(text)
    if not m:
        raise SystemExit(f"{path}: 缺少 frontmatter（--- name/description ---）")
    front = m.group(1)
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    if not name or not desc:
        raise SystemExit(f"{path}: frontmatter 缺 name 或 description")
    return {
        "name": name.group(1).strip(),
        "description": desc.group(1).strip(),
        "content": text.replace(desc.group(0), "", 1).replace(
            name.group(0), "", 1).strip() if False else text,
    }


def build(key: str) -> Path:
    spec = SUITES[key]
    skills = []
    for skill in spec["skills"]:
        path = PRESET_ROOT / skill / "SKILL.md"
        if not path.exists():
            raise SystemExit(f"技能稿不存在：{path}")
        skills.append(parse_skill(path))

    doc = {
        "name": spec["name"],
        "description": spec["description"],
        "tags": spec["tags"],
        "visibility": "public",
        "mcpServers": spec["mcp_servers"],
        "agents": [{
            "id": f"pack-{spec['suite_id']}-analyst",
            "name": spec["name"].replace("套件", "助手"),
            "persona": spec["persona"],
        }],
        "skills": skills,
        "_suite_ref": {
            "suite_schema": "facet-preset-suite/v1",
            "suite_id": spec["suite_id"],
            "entry_skill": spec["entry_skill"],
            "data_caliber": spec["data_caliber"],
            "generated_by": "finddata-skills/scripts/build_wire_suite.py",
            "note": "本文件由技能稿生成，请勿手改；改技能稿后重跑生成器",
        },
    }
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    out = OUT_ROOT / f"{spec['suite_id']}.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def refresh_all() -> list[tuple[str, int]]:
    """把每个套件快照里各技能的 description/content 与 SKILL.md 同步。

    只改这两个字段，其余（mcpServers / agents / _suite_ref / tags）原样保留——
    结构的真源是快照本身，正文的真源是技能稿。这样既不会手抄正文，也不会让
    生成器去猜每个套件的组成。
    """
    results: list[tuple[str, int]] = []
    for path in sorted(OUT_ROOT.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        changed = 0
        for skill in doc.get("skills", []):
            name = skill.get("name")
            src = PRESET_ROOT / str(name) / "SKILL.md"
            if not src.exists():
                # 没有本地授权稿 = 该技能只存在于市场（已发布产物）。
                # 快照里那份正文是**市场内容的镜像**，不能用本地文件覆盖，
                # 也不能假装同步过——刷新必须读市场 API（GET /api/packs/<id>）。
                print(f"  [market-only] {path.name}: {name} 无本地授权稿，"
                      f"快照来自市场，刷新须读市场 API")
                continue
            fresh = parse_skill(src)
            if skill.get("description") != fresh["description"] or \
                    skill.get("content") != fresh["content"]:
                skill["description"] = fresh["description"]
                skill["content"] = fresh["content"]
                changed += 1
        if changed:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        results.append((path.name, changed))
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("suite", nargs="?", default="macros", choices=sorted(SUITES),
                    help="套件键（生成/覆盖该套件快照）")
    ap.add_argument("--refresh", action="store_true",
                    help="把全部快照里各技能的 description/content 与技能稿同步（不动结构）")
    args = ap.parse_args(argv)
    if args.refresh:
        results = refresh_all()
        total = sum(n for _, n in results)
        for name, n in results:
            print(f"  {name:<40} {'更新 ' + str(n) + ' 个技能' if n else '无变化'}")
        print(f"合计更新 {total} 个技能正文")
        return 0
    out = build(args.suite)
    print(f"已生成 {out.relative_to(REPO)}")
    doc = json.loads(out.read_text())
    total = sum(len(s["content"]) for s in doc["skills"])
    print(f"  技能数 {len(doc['skills'])}，正文合计 {total} 字符，"
          f"mcpServers {len(doc['mcpServers'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
