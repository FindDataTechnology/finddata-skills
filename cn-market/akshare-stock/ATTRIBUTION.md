# Attribution

## Upstream

- Repository: https://github.com/molezzz/openclaw-stock-skill
- Commit: 5ba4edb (fix(news): scrape eastmoney finance home via agent-browser)
- License: MIT (declared in upstream README.md "License" section)
- Files adapted: SKILL.md, main.py, router.py, formatter.py, README.md, USER_MANUAL.md, adapters/__init__.py, adapters/akshare_adapter.py

## Local modifications (FindData adaptation)

1. SKILL.md frontmatter: removed the OpenClaw-specific `metadata.openclaw` block (emoji, `requires.python_modules`); the Python requirements (Python 3.9+, akshare / pandas / numpy) were moved into the body text as a portable statement.
2. SKILL.md: removed the author-machine akshare site-packages path (an absolute path inside the original author's home directory) and the "Mac + Python 3.9" environment line; replaced with a platform-neutral requirement statement.
3. SKILL.md: updated the suggested skill entry point from `python3 skills/akshare-stock/main.py ...` to `python3 cn-market/akshare-stock/main.py ...` to match this repository's layout.
4. SKILL.md: inserted a "FindData Data Sources" note after the architecture section (section 1) describing how to implement a FindData MCP adapter (`fd-open-data-mcp` / `fd-find-data-business-mcp`) alongside the default akshare fallback.
5. adapters/akshare_adapter.py: replaced the hardcoded absolute font path for `msyh.ttf` (which embedded the original author's home directory) with `os.path.expanduser('~/Library/Fonts/msyh.ttf')` in the Chinese-font fallback list (same behavior, machine-independent).
6. Added this ATTRIBUTION.md.

Not copied from upstream: `.gitignore` (repository packaging metadata, not part of the skill).

## Notes

- `main.py` (VOLUME_ANALYSIS intent) optionally shells out to a sibling skill script resolved via a relative path (`<repo>/a-stock-analysis/scripts/analyze.py`). That sibling is not part of this skill; when absent the intent returns a graceful error instead of crashing.
- Upstream README.md / USER_MANUAL.md were copied verbatim (usage examples keep the upstream `python main.py --query ...` form, to be run from this directory).
