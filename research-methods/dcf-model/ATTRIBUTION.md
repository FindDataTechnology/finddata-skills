# Attribution

- **Upstream repository**: https://github.com/anthropics/financial-services
- **Upstream commit**: 35c80df (35c80df9f4fb49f7888c681242a690dcde403f24)
- **License**: Apache-2.0
- **Source path in upstream repo**: `plugins/agent-plugins/model-builder/skills/dcf-model`

## Local modifications

Frontmatter cleanup, FindData MCP data-source priority injected, runtime placeholders removed.

Details:

- **Frontmatter cleanup**: retained only `name` and `description`; runtime-specific fields removed (none were present in this upstream file).
- **FindData MCP data-source priority injected**: FindData MCP servers (`fd-open-data-mcp` / `fd-find-data-business-mcp`) were inserted as item 1 of the "Data Sources Priority" list in Step 1 of `SKILL.md`; the original sources (other MCP servers, user-provided data, web search) were retained as fallbacks.
- **Runtime placeholders removed**: runtime path placeholders and machine-specific absolute paths were checked for and removed (none were present in this upstream file).
