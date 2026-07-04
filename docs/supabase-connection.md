# Supabase Connection

This project is configured for the hosted Supabase MCP server through `.mcp.json`.

Current local MCP URL:

```text
https://mcp.supabase.com/mcp?read_only=true
```

Use the browser OAuth flow in the MCP client and log in with the Supabase account that owns the Marketing Swipe File project. Do not use the currently visible `crm-ia` project for this workspace.

After the correct Supabase project exists, scope MCP to that project:

```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp?project_ref=<project-ref>&read_only=true"
    }
  }
}
```

Keep `read_only=true` for inspection. Remove it only when intentionally applying migrations or running write operations.

Secrets stay local:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ACCESS_TOKEN`

Use `.env` or `.mcp.local.json` for local-only values. Both are ignored by Git.
