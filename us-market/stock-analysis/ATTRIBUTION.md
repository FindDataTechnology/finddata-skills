# Attribution

## Upstream

- Repository: https://github.com/claude-office-skills/skills
- Commit: 9c4c7d5 (feat: add 5 pre-built agents with AGENT.md specs)
- License: MIT
- Source path in upstream repo: `skills/stock-analysis/SKILL.md` (single-file skill)

## Local modifications (FindData adaptation)

1. SKILL.md frontmatter: removed the `# ═══ CLAUDE OFFICE SKILL ═══` comment block and the loose extra fields (author, tags, department, models, mcp, capabilities, languages, related_skills, quoted values); rewrote as clean standard YAML frontmatter keeping only `name`, `description`, `version`, `license: MIT`, `category: finance`.
2. SKILL.md: inserted a "FindData Data Sources" note immediately after the first `#` heading, preferring FindData MCP servers (`fd-open-data-mcp` / `fd-find-data-business-mcp`) as the primary source for market fundamentals and indicator data when available.
3. Added this ATTRIBUTION.md.

Body content (analysis frameworks, metric tables, output format, example, tips, limitations) is unchanged from upstream.
