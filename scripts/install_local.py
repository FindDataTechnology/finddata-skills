#!/usr/bin/env python3
"""Install finddata-skills into local coding-agent skill directories.

Copies every repo skill (category/<name>/SKILL.md) into the personal skill
directories of the supported coding agents, so the same team skill works in
ZCode and Claude Code alike:

  - ZCode:       ~/.zcode/skills/<name>/   and   ~/.agents/skills/<name>/
  - Claude Code: ~/.claude/skills/<name>

All agents read the same open SKILL.md format (YAML frontmatter with
`name` + `description`), so no content transformation is needed — the
installer is a straight copy, idempotent by default (only overwrites when
the repo copy differs from the installed one; `--force` re-copies anyway).

Usage:
  python3 scripts/install_local.py                # sync all skills
  python3 scripts/install_local.py --list         # show what would be installed
  python3 scripts/install_local.py --only xingyan-publish data-analysis
  python3 scripts/install_local.py --force        # recopy even when identical

Notes:
  - Installed copies are working copies: edit the REPO, re-run the installer.
    A banner comment is prepended to each installed SKILL.md pointing back
    here so future sessions know where the truth lives.
  - Skills are keyed by NAME (not category) because every agent discovers
    skills as ~/.<tool>/skills/<name>/SKILL.md. Duplicate names across
    categories are refused at scan time.
"""
import argparse
import filecmp
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ZCode reads both of these; Claude Code reads the first one.
TARGETS = {
    "zcode": Path.home() / ".zcode" / "skills",
    "agents": Path.home() / ".agents" / "skills",
    "claude-code": Path.home() / ".claude" / "skills",
}

BANNER = (
    "<!--\n  finddata-skills 安装副本（真源: FindDataTechnology/finddata-skills"
    " {category}/{name}）。\n  改技能请改仓库后重跑 scripts/install_local.py；"
    "直接改这里会被下次安装覆盖。\n-->\n\n"
)


def scan():
    """Every category/*/SKILL.md in the repo → {(category, name): skill_dir}."""
    found = {}
    for category_dir in sorted(p for p in REPO.iterdir() if p.is_dir()):
        if category_dir.name.startswith((".", "scripts")):
            continue
        for skill_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
            if (skill_dir / "SKILL.md").is_file():
                name = skill_dir.name
                if name in found:
                    sys.exit(f"duplicate skill name across categories: {name}")
                found[name] = (category_dir.name, skill_dir)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="list skills and targets, no writes")
    ap.add_argument("--only", nargs="*", help="restrict to these skill names")
    ap.add_argument("--force", action="store_true", help="recopy even when identical")
    args = ap.parse_args()

    skills = scan()
    if args.only:
        missing = set(args.only) - set(skills)
        if missing:
            sys.exit(f"unknown skill(s): {sorted(missing)}")
        skills = {k: v for k, v in skills.items() if k in args.only}

    if args.list:
        for name, (category, _) in sorted(skills.items()):
            print(f"{category}/{name}")
        print(f"\ntargets: " + ", ".join(str(t) for t in TARGETS.values()))
        return

    installed = copied = 0
    for name, (category, src) in sorted(skills.items()):
        for tool, base in TARGETS.items():
            dest_dir = base / name
            dest = dest_dir / "SKILL.md"
            dest_dir.mkdir(parents=True, exist_ok=True)
            tmp = dest_dir / ".SKILL.md.incoming"
            tmp.write_text(BANNER.format(category=category, name=name) + (src / "SKILL.md").read_text())
            if args.force or not dest.exists() or not filecmp.cmp(tmp, dest, shallow=False):
                shutil.move(str(tmp), str(dest))
                copied += 1
            else:
                tmp.unlink()
            # side-car files (scripts/, references/ …) ride along verbatim
            for child in src.iterdir():
                if child.name == "SKILL.md":
                    continue
                side = dest_dir / child.name
                if child.is_dir():
                    if not side.exists() or not filecmp.dircmp(child, side).diff_files == []:
                        shutil.rmtree(side, ignore_errors=True)
                        shutil.copytree(child, side)
                elif args.force or not side.exists() or not filecmp.cmp(child, side, shallow=False):
                    shutil.copy2(child, side)
            installed += 1
    print(f"installed {installed} skill(s) into {len(TARGETS)} target(s); {copied} file set(s) updated")


if __name__ == "__main__":
    main()
