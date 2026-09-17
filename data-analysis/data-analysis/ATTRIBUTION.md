# Attribution — data-analysis

- **Upstream repository**: https://github.com/claude-office-skills/skills
- **Upstream commit**: 9c4c7d5
- **License**: MIT (author: claude-office-skills)
- **Upstream path**: `skills/data-analysis/SKILL.md` (single-file skill)

## Local changes (FindData adaptation)

1. **Frontmatter rewritten** in `SKILL.md`: the original "CLAUDE OFFICE SKILL - Enhanced
   Metadata v2.0" comment-annotated block (which mixed comment banners and loose,
   non-standard keys such as `models`, `mcp`, `capabilities`, `input`, `output`,
   `languages`, `related_skills`, `tags`, `department`) was replaced with standard YAML
   keeping only `name`, `description`, `version`, `license: MIT`, and
   `category: data-analysis` (upstream had `category: finance`; recategorized to match the
   FindData target directory). The `description` and `version` values are unchanged from
   upstream.
2. **FindData note inserted** immediately after the first `#` heading of `SKILL.md`,
   directing indicator/macro/entity series loading to FindData MCP servers
   (`fd-open-data-mcp` / `fd-find-data-business-mcp`, tools `read`, `read_range`,
   `list_concepts`).
3. **Added this ATTRIBUTION.md**.

All body content below the frontmatter is otherwise unchanged from upstream commit 9c4c7d5.
