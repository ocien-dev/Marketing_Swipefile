# Supabase Connection

This project can connect to the hosted Supabase MCP server without changing the globally connected Supabase account in Codex.

Use the project-scoped Codex config in `.codex/config.toml`. That file is intentionally ignored by Git.

Tracked example:

```text
.codex/config.example.toml
```

Local-only active config:

```text
.codex/config.toml
```

## Local setup

1. In the Supabase account that owns Marketing Swipe File, copy the project ref.
2. Create a Supabase access token for local MCP usage.
3. Set the token in your shell/user environment as `MSF_SUPABASE_ACCESS_TOKEN`.
4. Edit `.codex/config.toml` locally:
   - replace `REPLACE_WITH_MSF_SUPABASE_PROJECT_REF`
   - set `enabled = true`
5. Reload/reopen the Codex project so the MCP server is discovered.

PowerShell example for the current terminal:

```powershell
$env:MSF_SUPABASE_ACCESS_TOKEN = "sbp_..."
```

Optional persistent user environment:

```powershell
[Environment]::SetEnvironmentVariable("MSF_SUPABASE_ACCESS_TOKEN", "sbp_...", "User")
```

## Codex MCP config

```toml
[mcp_servers.supabase_msf]
url = "https://mcp.supabase.com/mcp?project_ref=<project-ref>&read_only=true"
bearer_token_env_var = "MSF_SUPABASE_ACCESS_TOKEN"
enabled = true
```

Keep `read_only=true` for inspection. Remove it only when intentionally applying migrations or running write operations.

The committed `.mcp.json` is a generic MCP-client fallback that also uses environment variables instead of OAuth. Codex itself should use `.codex/config.toml`.

Secrets stay local:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ACCESS_TOKEN`
- `MSF_SUPABASE_ACCESS_TOKEN`

Use `.env`, `.mcp.local.json`, or `.codex/config.toml` for local-only values. All are ignored by Git.
