# Vibenote MCP Server

Exposes your Vibenote vault as tools for any MCP client — Claude Desktop, VS Code, Cursor, Windsurf, or any tool that supports the Model Context Protocol.

## What it does

Six tools, accessible from any MCP-compatible AI assistant:

| Tool | What it does |
|---|---|
| `vibenote_capture` | Capture a thought, quote, or note into the vault |
| `vibenote_list_threads` | List all threads with descriptions |
| `vibenote_read_thread` | Read a thread's synthesized structured note |
| `vibenote_list_concepts` | List cross-thread concept cards |
| `vibenote_read_concept` | Read a concept card |
| `vibenote_process` | Trigger concept extraction (~1-2 minutes) |

The MCP server is a **data provider** — it gives the client LLM access to your vault. The client LLM (Claude, GPT, etc.) does the thinking and synthesis. No extra LLM calls from the server side.

## Setup for Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vibenote": {
      "command": "python3",
      "args": ["/path/to/.vibenote/bin/vibenote-mcp.py"],
      "env": {
        "VIBENOTE_HOME": "/path/to/.vibenote"
      }
    }
  }
}
```

Restart Claude Desktop. The tools appear automatically.

## Setup for VS Code

Add to your VS Code settings (or `.vscode/mcp.json`):

```json
{
  "mcp": {
    "servers": {
      "vibenote": {
        "command": "python3",
        "args": ["/path/to/.vibenote/bin/vibenote-mcp.py"],
        "env": {
          "VIBENOTE_HOME": "/path/to/.vibenote"
        }
      }
    }
  }
}
```

## How it works

```
MCP Client (Claude Desktop / VS Code / Cursor)
    ↓ JSON-RPC over stdio
vibenote-mcp.py
    ↓ imports
vibenote-bridge.py (vault operations)
    ↓ reads/writes
~/.vibenote/ (threads, concepts, index)
```

The MCP server imports the bridge module directly — same code that powers the Chrome extension. No duplication.

Zero dependencies beyond Python stdlib. Protocol is JSON-RPC 2.0 with Content-Length framing (like LSP), implemented inline.

## Example usage in Claude Desktop

**Capture from a conversation:**
> "Save to Vibenote: the key insight from our discussion is that DPO with 500 preference pairs is enough for initial tutor alignment"

Claude calls `vibenote_capture` → filed to the right thread(s) automatically.

**Query your vault:**
> "What are my open questions in Vibenote?"

Claude calls `vibenote_list_threads` → `vibenote_read_thread` for each → synthesizes an answer from your structured notes.

**Explore connections:**
> "What concepts connect my research threads?"

Claude calls `vibenote_list_concepts` → `vibenote_read_concept` for each → explains the cross-thread connections.

## Architecture note

The MCP server does NOT call Claude for synthesis — the client LLM does that. This means:
- No subprocess calls to `claude -p`
- No extra API costs
- Works with any MCP client (not just Claude)
- The quality of synthesis depends on the client LLM
