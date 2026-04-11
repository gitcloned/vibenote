#!/usr/bin/env python3
"""
Vibenote MCP Server — exposes the Vibenote vault as tools for any MCP client
(Claude Desktop, VS Code, Cursor, etc.)

Protocol: JSON-RPC 2.0 over stdio with line-delimited JSON.
Each message is a single JSON object followed by a newline. No framing headers.
Zero dependencies beyond Python stdlib.

Tools:
  vibenote_capture       — capture text to the vault
  vibenote_list_threads  — list all threads with descriptions
  vibenote_read_thread   — read a thread's structured note
  vibenote_list_concepts — list cross-thread concept cards
  vibenote_read_concept  — read a concept card
  vibenote_process       — trigger concept extraction
"""

import json
import os
import re
import sys
import importlib.util
from pathlib import Path

# ---------- Import the bridge module for vault operations ----------

VIBENOTE_HOME = Path(os.environ.get("VIBENOTE_HOME", Path.home() / ".vibenote"))
BRIDGE_PATH = VIBENOTE_HOME / "bin" / "vibenote-bridge.py"

# Fallback: look in the repo directory structure
if not BRIDGE_PATH.exists():
    BRIDGE_PATH = Path(__file__).parent.parent / "bridge" / "vibenote-bridge.py"

if BRIDGE_PATH.exists():
    spec = importlib.util.spec_from_file_location("bridge", str(BRIDGE_PATH))
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
else:
    print(f"vibenote-mcp: bridge not found at {BRIDGE_PATH}", file=sys.stderr)
    sys.exit(1)


# ---------- MCP Protocol (JSON-RPC 2.0 over stdio, line-delimited JSON) ----------

def read_message():
    """Read one line-delimited JSON-RPC message from stdin."""
    line = sys.stdin.buffer.readline()
    if not line:
        return None  # EOF
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line.decode("utf-8"))
    except json.JSONDecodeError as e:
        log(f"JSON decode error on line: {line[:200]} — {e}")
        return None


def write_message(msg):
    """Write one line-delimited JSON-RPC message to stdout."""
    body = json.dumps(msg).encode("utf-8") + b"\n"
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def respond(id, result):
    write_message({"jsonrpc": "2.0", "id": id, "result": result})


def respond_error(id, code, message):
    write_message({"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}})


def log(msg):
    print(f"vibenote-mcp: {msg}", file=sys.stderr, flush=True)


# ---------- Tool definitions ----------

TOOLS = [
    {
        "name": "vibenote_capture",
        "description": "Capture a thought, quote, or note into the Vibenote vault. The system classifies which thread(s) it belongs to, or you can specify a thread explicitly. A capture can be filed to multiple threads if relevant.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The text to capture — a thought, quote, paste, or anything"},
                "title": {"type": "string", "description": "Optional title or source name"},
                "url": {"type": "string", "description": "Optional source URL"},
                "thread": {"type": "string", "description": "Optional thread slug to file to. Leave empty for automatic classification."},
            },
            "required": ["content"],
        },
    },
    {
        "name": "vibenote_list_threads",
        "description": "List all threads in the Vibenote vault with their descriptions, entry counts, and last updated dates. Use this to discover what topics the user has been capturing about.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vibenote_read_thread",
        "description": "Read a thread's full structured note (synthesized summary), description, and metadata. The structured note is a synthesis of all journal entries in the thread — it contains the user's current understanding of the topic, key decisions, open questions, and references.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "The thread slug (e.g. 'ai-education-research')"},
            },
            "required": ["slug"],
        },
    },
    {
        "name": "vibenote_list_concepts",
        "description": "List all cross-thread concept cards in the vault. Concepts are ideas that appear meaningfully in 2+ threads — they represent connections between different areas of the user's thinking. Each has a strength score reflecting how central and recent it is.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "vibenote_read_concept",
        "description": "Read a concept card — a compressed synthesis of how one idea appears across multiple threads. Concept cards name the pattern, state the key tension, pose one open question, and link to referencing threads.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "The concept slug (e.g. 'feedback-and-reward-signals')"},
            },
            "required": ["slug"],
        },
    },
    {
        "name": "vibenote_process",
        "description": "Trigger concept extraction across all threads. Reads all structured notes, identifies concepts that span 2+ threads, generates or updates concept cards, inserts wikilinks. This is a slow operation (~1-2 minutes) that should only be called when the user explicitly asks to process their vault.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ---------- Tool handlers ----------

def handle_capture(params):
    content = params.get("content", "").strip()
    title = params.get("title", "").strip()
    url = params.get("url", "").strip()
    thread = params.get("thread", "").strip()

    if not content and not title and not url:
        return text_result("Nothing to capture — provide content, title, or URL.")

    result = bridge.handle_capture({
        "content": content,
        "title": title,
        "url": url,
        "thread": thread or None,
    })

    if result.get("ok"):
        threads = result.get("threads", [result.get("thread", "unknown")])
        new = result.get("created_new", [])
        msg = f"Captured to: {', '.join(threads)}"
        if new:
            msg += f" (new thread{'s' if len(new) > 1 else ''}: {', '.join(new)})"
        return text_result(msg)
    else:
        return text_result(f"Capture failed: {result.get('error', 'unknown error')}")


def handle_list_threads(_params):
    result = bridge.handle_list_threads()
    threads = result.get("threads", [])
    if not threads:
        return text_result("No threads in the vault yet. Use vibenote_capture to start.")

    lines = [f"**{len(threads)} threads in vault:**\n"]
    for t in threads:
        desc = t.get("description") or t.get("summary", "")
        entries = t.get("entries", "?")
        updated = t.get("updated", "?")
        state = t.get("state", "")
        lines.append(f"- **{t['slug']}** ({entries} entries, updated {updated}, {state})")
        if desc:
            lines.append(f"  {desc}")
    return text_result("\n".join(lines))


def handle_read_thread(params):
    slug = params.get("slug", "").strip()
    if not slug:
        return text_result("Please provide a thread slug.")

    thread = bridge.load_thread_full(slug)
    if not thread:
        return text_result(f"Thread not found: {slug}")

    parts = [f"# {thread['title']}\n"]

    if thread.get("structured_note"):
        parts.append("## Structured Note\n")
        parts.append(thread["structured_note"])
    else:
        parts.append("*No structured note yet — thread has not been processed.*")

    parts.append(f"\n\n---\n*{slug} · journal has additional raw entries*")
    return text_result("\n".join(parts))


def handle_list_concepts(_params):
    result = bridge.handle_list_concepts()
    concepts = result.get("concepts", [])
    if not concepts:
        return text_result("No concepts yet. Run vibenote_process to extract cross-thread concepts.")

    active = [c for c in concepts if c.get("state") != "archived"]
    lines = [f"**{len(active)} active concepts:**\n"]
    for c in active:
        strength = c.get("strength", 0)
        threads = c.get("threads", [])
        desc = c.get("description", "")
        lines.append(f"- **{c['slug']}** (strength: {strength:.1f}, spans: {', '.join(threads)})")
        if desc:
            lines.append(f"  {desc}")
    return text_result("\n".join(lines))


def handle_read_concept(params):
    slug = params.get("slug", "").strip()
    if not slug:
        return text_result("Please provide a concept slug.")

    result = bridge.handle_read_concept({"slug": slug})
    if not result.get("ok"):
        return text_result(f"Concept not found: {slug}")

    return text_result(result.get("body", "(empty concept page)"))


def handle_process(_params):
    log("Starting concept extraction (this may take 1-2 minutes)...")
    result = bridge.handle_process_concepts({})
    if result.get("ok"):
        gen = result.get("concepts_generated", 0)
        upd = result.get("concepts_updated", 0)
        concepts = result.get("concepts", [])
        return text_result(
            f"Processing complete. {gen} new concepts, {upd} updated.\n"
            f"Concepts: {', '.join(concepts) if concepts else 'none'}"
        )
    else:
        return text_result(f"Processing failed: {result.get('error', 'unknown')}")


def text_result(text):
    """Wrap text in MCP's content format."""
    return {"content": [{"type": "text", "text": text}]}


TOOL_HANDLERS = {
    "vibenote_capture": handle_capture,
    "vibenote_list_threads": handle_list_threads,
    "vibenote_read_thread": handle_read_thread,
    "vibenote_list_concepts": handle_list_concepts,
    "vibenote_read_concept": handle_read_concept,
    "vibenote_process": handle_process,
}


# ---------- Main loop ----------

def main():
    log("Server starting...")

    while True:
        try:
            msg = read_message()
            if msg is None:
                break  # stdin closed

            method = msg.get("method", "")
            id = msg.get("id")
            params = msg.get("params", {})

            if method == "initialize":
                respond(id, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "vibenote", "version": "0.1.0"},
                })
                log("Initialized")

            elif method == "notifications/initialized":
                pass  # acknowledgment, no response needed

            elif method == "tools/list":
                respond(id, {"tools": TOOLS})

            elif method == "tools/call":
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                handler = TOOL_HANDLERS.get(tool_name)
                if handler:
                    try:
                        result = handler(tool_args)
                        respond(id, result)
                    except Exception as e:
                        log(f"Tool error ({tool_name}): {e}")
                        respond(id, text_result(f"Error: {e}"))
                else:
                    respond_error(id, -32601, f"Unknown tool: {tool_name}")

            elif method == "ping":
                respond(id, {})

            elif id is not None:
                # Unknown method with an id — respond with error
                respond_error(id, -32601, f"Method not found: {method}")
            # else: notification we don't handle, ignore

        except json.JSONDecodeError as e:
            log(f"JSON parse error: {e}")
        except Exception as e:
            log(f"Unexpected error: {e}")
            if id is not None:
                respond_error(id, -32603, str(e))


if __name__ == "__main__":
    main()
