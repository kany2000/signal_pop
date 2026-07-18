# External (install.sh) MCP Server Setup

Some MCP servers ship as standalone single binaries with their own `install.sh` — e.g. codebase-memory-mcp, KiloCode. Their install scripts auto-detect common coding agents (Claude-Code, Codex, OpenClaw) but **do NOT configure Hermes Agent**.

## Workflow

```bash
# 1. Run the project's install script
curl -fsSL https://raw.githubusercontent.com/.../main/install.sh | bash

# 2. Verify binary installed
which <binary> && <binary> version

# 3. Register with Hermes
hermes mcp add <name> --command <binary>

# 4. (optional) Pipe 'Y' to auto-enable all tools non-interactively
echo 'Y' | hermes mcp add <name> --command <binary>

# 5. Verify
hermes mcp list
hermes mcp test <name>
```

## Example — codebase-memory-mcp

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash
hermes mcp add codebase-memory-mcp --command codebase-memory-mcp
```

The install script configures Claude-Code (.mcp.json + hooks), Codex (.codex/config.toml + AGENTS.md), OpenClaw — but NOT Hermes. The `hermes mcp add` step saves the config to `~/.hermes/config.yaml` under `mcp_servers`:

```yaml
mcp_servers:
  codebase-memory-mcp:
    command: "codebase-memory-mcp"
    args: []
    env: {}
    timeout: 120
    connect_timeout: 60
```

## Notes

- `hermes mcp add --command <binary>` uses stdio transport
- No URL or args needed for simple binary servers (args default to `[]`)
- After adding, start a new session (`/reset`) for tools to appear
- Works for any binary-server on PATH, not just install.sh-distributed ones
