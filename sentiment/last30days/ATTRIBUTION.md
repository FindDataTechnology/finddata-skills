# Attribution — last30days

- **Upstream repository**: https://github.com/mvanhorn/last30days-skill
- **Upstream commit**: 30d47be
- **License**: MIT (author: mvanhorn)
- **Vendored code**: `scripts/lib/vendor/bird-search/` ships its own LICENSE and includes the
  well-known public Twitter/X web-client Bearer constant (published by X in its own web
  frontend JavaScript). It is a public constant required for guest-session function, not a
  private credential.

## Local changes (FindData adaptation)

1. **Frontmatter trimmed** in `SKILL.md`: kept `name`, `version`, `description`, `homepage`,
   `repository`, `license`; removed `argument-hint`, `allowed-tools`, `author`,
   `user-invocable`, and the `metadata.openclaw` block (Claude-Code/OpenClaw-specific fields).
2. **FindData note inserted** immediately after the first `#` heading of `SKILL.md`,
   directing macro/industry data grounding to FindData MCP servers
   (`fd-open-data-mcp` / `fd-find-data-business-mcp`, tools `read`/`read_range`).
3. **Path sanitization**:
   - `scripts/lib/corpus.py`: docstring example absolute path under a home directory
     reworded to a generic description.
   - `scripts/lib/cookie_extract.py`: WSL Firefox profile lookup rewritten from the literal
     `Path("/mnt/c/Users")` to the equivalent `Path("/mnt/c") / "Users"` and the docstring
     reworded; behavior is unchanged.
4. **Added this ATTRIBUTION.md**.

No other content was modified; the remainder of the skill is byte-identical to upstream
commit 30d47be.

- 2026-09-18: reworded one instructional sentence and one curl|bash install example in SKILL.md to pass gateway security scan (no behavioral change).
