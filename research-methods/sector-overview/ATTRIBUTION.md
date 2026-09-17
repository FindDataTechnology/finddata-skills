# Attribution

- **Upstream repository**: https://github.com/anthropics/financial-services
- **Upstream commit**: 35c80df (35c80df9f4fb49f7888c681242a690dcde403f24)
- **License**: Apache-2.0
- **Source path in upstream repo**: `plugins/agent-plugins/market-researcher/skills/sector-overview`

## Local modifications

Frontmatter cleanup, FindData MCP data-source priority injected, runtime placeholders removed.

Details:

- **Frontmatter cleanup**: retained only `name` and `description`; runtime-specific fields removed (none were present in this upstream file).
- **FindData MCP data-source priority injected**: a FindData Data Sources note was inserted after the first `#` heading of `SKILL.md`, directing preferential use of `fd-open-data-mcp` / `fd-find-data-business-mcp`.
- **Runtime placeholders removed**: runtime path placeholders and machine-specific absolute paths were checked for and removed (none were present in this upstream file).
