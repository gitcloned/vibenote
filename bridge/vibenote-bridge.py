#!/usr/bin/env python3
"""
Vibenote native messaging bridge.

Invoked by the Chrome extension via Chrome's native messaging protocol.
Reads a single framed JSON message from stdin, writes a single framed JSON
response to stdout, exits.

Message framing: 4-byte little-endian unsigned int (length) + UTF-8 JSON body.

Supported operations:
  - list-threads: Returns the list of threads from the index for the dropdown.
  - capture: Appends a journal entry to a thread. If no thread specified,
             auto-classifies using simple keyword matching.

All file operations target ~/.vibenote/ (or $VIBENOTE_HOME if set).
Never touches ## My Notes or ## Structured Note sections — journal only.
"""

import json
import os
import re
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

VIBENOTE_HOME = Path(os.environ.get("VIBENOTE_HOME", Path.home() / ".vibenote"))
THREADS_DIR = VIBENOTE_HOME / "threads"
INDEX_PATH = VIBENOTE_HOME / "meta" / "index.md"
CONFIG_PATH = VIBENOTE_HOME / "config.json"
UPDATE_INDEX_SCRIPT = VIBENOTE_HOME / "scripts" / "vn-update-index.sh"

MY_NOTES_PLACEHOLDER = (
    "*Your space. Vibenote never touches this section — "
    "add your own annotations, corrections, or commentary here freely.*"
)


# ---------- Native messaging protocol ----------

def read_message():
    """Read one framed message from stdin. Returns parsed JSON dict or None on EOF."""
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) < 4:
        return None
    length = struct.unpack("<I", raw_length)[0]
    body = sys.stdin.buffer.read(length).decode("utf-8")
    return json.loads(body)


def send_message(payload):
    """Write one framed message to stdout."""
    body = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(body)))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


# ---------- Vault helpers ----------

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(title):
    """Derive a hyphenated slug from a title. Max 40 chars, truncated at word boundaries."""
    slug = re.sub(r"[^a-z0-9\s-]", "", title.lower())
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    if len(slug) > 40:
        truncated = slug[:40]
        # Drop the last partial word if truncation cut mid-word.
        if "-" in truncated and not slug[40:41] in ("", "-"):
            truncated = truncated.rsplit("-", 1)[0]
        slug = truncated.rstrip("-")
    return slug or "untitled"


def read_index():
    """Parse ~/.vibenote/meta/index.md into a list of thread records."""
    if not INDEX_PATH.exists():
        return []
    threads = []
    with open(INDEX_PATH) as f:
        lines = f.readlines()
    in_table = False
    for line in lines:
        line = line.strip()
        if line.startswith("|---"):
            in_table = True
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.strip("|").split("|")]
            if not parts or parts[0] in ("slug", ""):
                continue
            if len(parts) >= 6:
                threads.append({
                    "slug": parts[0],
                    "state": parts[1],
                    "updated": parts[2],
                    "entries": parts[3],
                    "processed": parts[4],
                    "summary": parts[5],
                })
            elif len(parts) >= 4:
                threads.append({
                    "slug": parts[0],
                    "state": parts[1],
                    "updated": parts[2],
                    "entries": "",
                    "processed": "",
                    "summary": parts[-1],
                })
    # Enrich with descriptions from thread frontmatter (more useful than
    # index summaries for classification).
    for t in threads:
        desc_path = THREADS_DIR / f"{t['slug']}.md"
        if desc_path.exists():
            for fline in desc_path.read_text().splitlines():
                if fline.startswith("description:"):
                    t["description"] = fline[len("description:"):].strip()
                    break
    return threads


def llm_classify(title, url, content, threads, claude_bin, claude_dir, timeout=30):
    """
    Use Claude CLI to classify a capture into one or more threads.

    Returns {"threads": ["slug1", ...], "new_thread": null | {slug, title, description}}.
    Falls back to creating a new thread on any error.
    """
    if not threads:
        return {"threads": [], "new_thread": None}

    thread_list = "\n".join(
        f"- {t['slug']}: {t.get('description') or t.get('summary', '(no description)')}"
        for t in threads
    )

    capture_block = f"Title: {title}" if title else ""
    if url:
        capture_block += f"\nURL: {url}"
    if content:
        # Truncate very long content for the classify prompt — we need intent, not full text.
        short_content = content[:2000] + ("…" if len(content) > 2000 else "")
        capture_block += f"\nContent: {short_content}"

    prompt = f"""You are classifying a new capture for a personal knowledge base. Given the existing threads and the new capture, decide where it belongs.

Rules:
1. A capture can belong to MULTIPLE threads if it genuinely adds value to multiple topics.
2. Only match threads where the capture is clearly relevant — not just a vague keyword overlap.
3. If no existing thread is a good match, suggest a new one.
4. Be conservative: it's better to create a new thread than to misfile.

Existing threads:
{thread_list}

New capture:
{capture_block}

Return ONLY a valid JSON object (no markdown fences, no explanation) with these fields:
- "threads": array of matching thread slugs (can be empty if no match)
- "new_thread": null if existing threads match, or {{"slug": "...", "title": "...", "description": "..."}} if a new thread should be created

Examples:
{{"threads": ["slm-optimization-research", "ai-education-research"], "new_thread": null}}
{{"threads": [], "new_thread": {{"slug": "voice-ux-design", "title": "Voice UX Design", "description": "Design patterns for voice-first user interfaces"}}}}
{{"threads": ["reading-list"], "new_thread": null}}"""

    env = os.environ.copy()
    env["CLAUDE_CONFIG_DIR"] = claude_dir
    extra_paths = [
        str(Path(claude_bin).parent),
        "/opt/homebrew/bin",
        "/usr/local/bin",
        str(Path.home() / "Library" / "pnpm"),
        str(Path.home() / ".local" / "bin"),
    ]
    env["PATH"] = ":".join(extra_paths) + ":" + env.get("PATH", "/usr/bin:/bin")

    try:
        result = subprocess.run(
            [claude_bin, "-p", "--no-session-persistence", "--output-format", "text", "--tools", ""],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if result.returncode != 0:
            print(f"vibenote-bridge: classify LLM error (rc={result.returncode}): {result.stderr[:200]}", file=sys.stderr)
            return {"threads": [], "new_thread": None}

        raw = result.stdout.strip()
        # Strip markdown code fences if the model wraps its output.
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])
        raw = raw.strip()

        classification = json.loads(raw)
        # Validate structure.
        if not isinstance(classification.get("threads"), list):
            classification["threads"] = []
        # Filter to only slugs that actually exist.
        existing_slugs = {t["slug"] for t in threads}
        classification["threads"] = [s for s in classification["threads"] if s in existing_slugs]
        return classification

    except subprocess.TimeoutExpired:
        print("vibenote-bridge: classify LLM timed out", file=sys.stderr)
        return {"threads": [], "new_thread": None}
    except (json.JSONDecodeError, Exception) as e:
        print(f"vibenote-bridge: classify parse error: {e}", file=sys.stderr)
        return {"threads": [], "new_thread": None}


def thread_path(slug):
    return THREADS_DIR / f"{slug}.md"


def create_thread(slug, title, description=""):
    """Create a new thread file with the standard template."""
    ts = now_iso()
    desc = description or f"Thread about {title}"
    content = f"""---
slug: {slug}
description: {desc}
created: {ts}
updated: {ts}
entry_count: 0
---

# {title}

## Structured Note
*Not yet processed. Run the processing agent to generate.*

---

## My Notes
{MY_NOTES_PLACEHOLDER}

---

## Journal
"""
    THREADS_DIR.mkdir(parents=True, exist_ok=True)
    thread_path(slug).write_text(content)


def append_entry(slug, title, url, body):
    """Append a journal entry, update frontmatter. Never touches My Notes or Structured Note."""
    path = thread_path(slug)
    if not path.exists():
        create_thread(slug, title or slug)

    text = path.read_text()
    ts = now_iso()

    # Build the entry.
    # Bookmark mode: if there's no body, just the source line. Otherwise the
    # full structured entry with source + body.
    if url and title:
        source_line = f"**Source:** [{title}]({url})"
    elif url:
        source_line = f"**Source:** {url}"
    elif title:
        source_line = f"**Title:** {title}"
    else:
        source_line = ""

    parts = [f"### {ts}"]
    if source_line:
        parts.append(source_line)
    if body:
        parts.append(body.strip())
    entry = "\n\n".join(parts) + "\n"

    # Append after the "## Journal" heading, at the end of the file.
    if "## Journal" not in text:
        # Old thread without journal section — shouldn't happen, but handle it.
        text = text.rstrip() + "\n\n## Journal\n"
    if not text.endswith("\n"):
        text += "\n"
    text += "\n" + entry

    # Update frontmatter: updated, entry_count.
    def bump_entry_count(match):
        current = int(match.group(1))
        return f"entry_count: {current + 1}"

    text = re.sub(r"^updated:\s*.*$", f"updated: {ts}", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^entry_count:\s*(\d+)\s*$", bump_entry_count, text, count=1, flags=re.MULTILINE)

    path.write_text(text)


def regenerate_index():
    """Run the vault's index regenerator. Safe to ignore errors — capture already succeeded."""
    if UPDATE_INDEX_SCRIPT.exists():
        try:
            subprocess.run(
                ["bash", str(UPDATE_INDEX_SCRIPT)],
                check=False,
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass


# ---------- Operation handlers ----------

def handle_list_threads():
    return {"ok": True, "threads": read_index()}


# ---------- Config + Ask ----------

def load_config():
    """Load ~/.vibenote/config.json. Returns a dict of known fields with safe defaults."""
    defaults = {
        "claude_config_dir": "~/.claude",
        "ask": {"timeout_seconds": 45, "model": None},
    }
    if not CONFIG_PATH.exists():
        return defaults
    try:
        raw = json.loads(CONFIG_PATH.read_text())
        defaults["claude_config_dir"] = raw.get("claude_config_dir", defaults["claude_config_dir"])
        ask = raw.get("ask") or {}
        defaults["ask"]["timeout_seconds"] = int(ask.get("timeout_seconds", 45))
        defaults["ask"]["model"] = ask.get("model")
    except Exception as e:
        print(f"vibenote-bridge: config.json parse error: {e}", file=sys.stderr)
    return defaults


def expand_path(p):
    """Expand ~ and $VARS in a path string."""
    return str(Path(os.path.expandvars(os.path.expanduser(p))))


def find_claude_binary():
    """
    Find the absolute path to the claude CLI binary.

    Chrome native messaging spawns the bridge with a minimal PATH that usually
    doesn't include wherever the user installed claude (pnpm, homebrew, etc).
    Shell aliases don't help because they only exist inside shells. So we look
    in common install locations and fall back to asking the user's login shell.
    """
    candidates = [
        Path.home() / "Library" / "pnpm" / "claude",      # pnpm global install
        Path("/opt/homebrew/bin/claude"),                  # Apple Silicon homebrew
        Path("/usr/local/bin/claude"),                     # Intel homebrew / classic
        Path.home() / ".local" / "bin" / "claude",         # pipx / per-user install
        Path.home() / ".claude" / "local" / "bin" / "claude",  # Claude Code self-install
        Path.home() / "bin" / "claude",                    # user bin convention
        Path.home() / ".npm" / "bin" / "claude",           # npm global
        Path.home() / ".volta" / "bin" / "claude",         # volta
    ]
    for p in candidates:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)

    # Fall back to asking the user's login shell where claude is. This picks up
    # PATH additions from .zshrc / .bash_profile that the direct search missed.
    for shell in ("/bin/zsh", "/bin/bash"):
        if not Path(shell).exists():
            continue
        try:
            result = subprocess.run(
                [shell, "-l", "-c", "command -v claude"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                path = result.stdout.strip().split("\n")[-1]
                if path and Path(path).is_file():
                    return path
        except Exception:
            continue
    return None


def extract_section(text, heading):
    """Extract the content of a '## Heading' section, stopping at the next '## ' heading."""
    in_block = False
    lines = []
    for line in text.splitlines():
        if line.startswith(f"## {heading}"):
            in_block = True
            continue
        if in_block and line.startswith("## "):
            break
        if in_block:
            lines.append(line)
    return "\n".join(lines).strip()


def load_all_structured_notes():
    """
    Read every thread file and extract its Structured Note section.
    Returns a list of {slug, structured_note} dicts, skipping threads with
    unprocessed or empty structured notes.
    """
    results = []
    if not THREADS_DIR.exists():
        return results
    for f in sorted(THREADS_DIR.glob("*.md")):
        slug = f.stem
        text = f.read_text()
        note = extract_section(text, "Structured Note")
        if not note:
            continue
        low = note.lower()
        if low.startswith("*not yet processed") or low.startswith("*too little content"):
            continue
        results.append({"slug": slug, "structured_note": note})
    return results


def load_thread_full(slug):
    """
    Load a single thread's structured note + full journal for thread-scoped
    ask queries. Returns {slug, title, structured_note, journal} or None if the
    thread doesn't exist.
    """
    path = THREADS_DIR / f"{slug}.md"
    if not path.exists():
        return None
    text = path.read_text()

    # Extract title from the first '# ' heading after frontmatter.
    title = slug
    for line in text.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            break

    structured = extract_section(text, "Structured Note")
    journal = extract_section(text, "Journal")

    # Truncate very long journals so we don't blow the context window. Keep the
    # most recent entries by splitting on '### ' timestamps and taking the tail.
    MAX_JOURNAL_CHARS = 40000
    if len(journal) > MAX_JOURNAL_CHARS:
        entries = re.split(r"(?=^### )", journal, flags=re.MULTILINE)
        # Keep entries from the end until we're under the limit.
        kept = []
        total = 0
        for entry in reversed(entries):
            if total + len(entry) > MAX_JOURNAL_CHARS:
                break
            kept.append(entry)
            total += len(entry)
        journal = "".join(reversed(kept))
        journal = "(earlier entries omitted for length)\n\n" + journal

    return {
        "slug": slug,
        "title": title,
        "structured_note": structured,
        "journal": journal,
    }


def build_corpus_prompt(question, notes):
    """Prompt for corpus-wide ask: uses structured notes from every thread."""
    if not notes:
        notes_block = "(vault is empty — no structured notes available)"
    else:
        parts = []
        for n in notes:
            parts.append(f"=== {n['slug']} ===\n{n['structured_note']}")
        notes_block = "\n\n".join(parts)

    return f"""You are answering a question from a personal knowledge base. The notes below are synthesized summaries the user has captured from their own thinking across multiple topics.

Rules:
1. Answer ONLY based on the notes below. Never invent content, never use outside knowledge.
2. Cite every claim with the thread slug inline, in the format (from <slug>). Use this exact format even when you group the answer by thread with headers — the citations are parsed by the UI to create clickable links.
3. If the answer isn't in the notes, say so plainly: "Nothing in your notes directly addresses this."
4. Be concise. 2-4 short paragraphs or a bulleted list. No filler.
5. Write in a calm, factual tone — you're helping the user recall their own thinking, not selling them anything.

NOTES:

{notes_block}

QUESTION: {question}"""


def build_thread_prompt(question, thread):
    """Prompt for thread-scoped ask: uses one thread's full content (structured note + journal)."""
    structured = thread["structured_note"] or "(no structured note yet — this thread is unprocessed)"
    journal = thread["journal"] or "(no journal entries yet)"

    return f"""You are answering a question about a single thread from the user's personal knowledge base. The thread has two parts: a synthesized structured note (the user's current understanding), and a journal of raw captures (the source material).

Rules:
1. Answer ONLY based on the thread below. Never invent content, never use outside knowledge.
2. Prefer the structured note for high-level answers ("what have I decided", "what's the current state"). Drill into the journal for specific quotes, sources, or details the structured note doesn't cover.
3. Cite specific journal entries by their timestamp when you reference them, like (entry from 2026-04-02).
4. If the answer isn't in the thread, say so plainly: "Nothing in this thread directly addresses that."
5. Be concise. 2-4 short paragraphs or a bulleted list. No filler.
6. Write in a calm, factual tone — you're helping the user recall their own thinking, not selling them anything.

THREAD: {thread['title']} (slug: {thread['slug']})

## Structured Note
{structured}

## Journal
{journal}

QUESTION: {question}"""


def handle_ask(payload):
    question = (payload.get("question") or "").strip()
    if not question:
        return {"ok": False, "error": "Empty question."}

    scope_slug = (payload.get("thread") or "").strip()

    config = load_config()
    claude_dir = expand_path(config["claude_config_dir"])
    timeout = config["ask"]["timeout_seconds"]
    model = config["ask"]["model"]

    # Locate the claude binary. Chrome spawns this bridge with a minimal PATH,
    # so we have to resolve the absolute path ourselves.
    claude_bin = find_claude_binary()
    if not claude_bin:
        return {
            "ok": False,
            "error": "claude CLI not found in common install locations. Make sure Claude Code is installed. If it is, let me know where `which claude` resolves to in your shell.",
        }

    # Build the prompt based on scope.
    if scope_slug:
        thread = load_thread_full(scope_slug)
        if not thread:
            return {"ok": False, "error": f"Thread not found: {scope_slug}"}
        prompt = build_thread_prompt(question, thread)
        notes_count = 1
        scope_label = scope_slug
    else:
        notes = load_all_structured_notes()
        prompt = build_corpus_prompt(question, notes)
        notes_count = len(notes)
        scope_label = "all threads"

    cmd = [
        claude_bin,
        "-p",
        "--no-session-persistence",
        "--output-format", "text",
        "--tools", "",
    ]
    if model:
        cmd.extend(["--model", model])

    # Augment PATH so that anything claude itself shells out to (node, etc.)
    # resolves correctly even though Chrome gave us a minimal env.
    env = os.environ.copy()
    env["CLAUDE_CONFIG_DIR"] = claude_dir
    extra_paths = [
        str(Path(claude_bin).parent),
        "/opt/homebrew/bin",
        "/usr/local/bin",
        str(Path.home() / "Library" / "pnpm"),
        str(Path.home() / ".local" / "bin"),
    ]
    env["PATH"] = ":".join(extra_paths) + ":" + env.get("PATH", "/usr/bin:/bin")

    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "claude CLI not found. Make sure Claude Code is installed and `claude` is on PATH.",
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": f"Query timed out after {timeout}s. Try a simpler question or raise ask.timeout_seconds in ~/.vibenote/config.json.",
        }

    elapsed_ms = int((time.time() - t0) * 1000)

    if result.returncode != 0:
        stderr_short = (result.stderr or "").strip()[:500]
        return {
            "ok": False,
            "error": f"claude exited with code {result.returncode}: {stderr_short}",
            "latency_ms": elapsed_ms,
        }

    answer = (result.stdout or "").strip()
    if not answer:
        return {
            "ok": False,
            "error": "claude returned an empty response.",
            "latency_ms": elapsed_ms,
        }

    # Extract cited slugs from the answer for UI highlighting.
    cited_slugs = sorted(set(re.findall(r"\(from ([a-z0-9][a-z0-9-]*)\)", answer)))

    return {
        "ok": True,
        "answer": answer,
        "latency_ms": elapsed_ms,
        "cited_slugs": cited_slugs,
        "thread_count": notes_count,
        "scope": scope_label,
        "scope_slug": scope_slug or None,
        "claude_config_dir": claude_dir,
    }


def handle_capture(payload):
    title = (payload.get("title") or "").strip()
    url = (payload.get("url") or "").strip()
    body = (payload.get("content") or "").strip()
    requested_thread = (payload.get("thread") or "").strip()

    if not body and not title and not url:
        return {"ok": False, "error": "Nothing to capture — no title, URL, or content."}

    config = load_config()
    claude_dir = expand_path(config["claude_config_dir"])
    threads = read_index()
    existing_slugs = {t["slug"] for t in threads}

    filed_to = []       # slugs the entry was filed to
    created_new = []    # slugs of newly created threads

    if requested_thread:
        # User explicitly picked a thread — skip LLM, file directly.
        if requested_thread not in existing_slugs:
            create_thread(requested_thread, title or requested_thread)
            created_new.append(requested_thread)
        append_entry(requested_thread, title, url, body)
        filed_to.append(requested_thread)
    else:
        # LLM classification — may return multiple threads.
        claude_bin = find_claude_binary()
        if claude_bin:
            classification = llm_classify(title, url, body, threads, claude_bin, claude_dir)
        else:
            # No claude binary — fall back to filing to a new thread.
            classification = {"threads": [], "new_thread": None}

        matched_slugs = classification.get("threads", [])
        new_thread_info = classification.get("new_thread")

        # File to matched threads.
        for slug in matched_slugs:
            append_entry(slug, title, url, body)
            filed_to.append(slug)

        # If LLM suggested a new thread and no existing match (or in addition).
        if new_thread_info and isinstance(new_thread_info, dict):
            new_slug = new_thread_info.get("slug", "")
            new_title = new_thread_info.get("title", title or new_slug)
            new_desc = new_thread_info.get("description", "")
            if new_slug:
                if new_slug in existing_slugs:
                    new_slug = f"{new_slug}-{now_iso()[:10]}"
                create_thread(new_slug, new_title, new_desc)
                append_entry(new_slug, title, url, body)
                filed_to.append(new_slug)
                created_new.append(new_slug)

        # Fallback: if LLM returned nothing useful, create a thread from the title.
        if not filed_to:
            fallback_slug = slugify(title) if title else slugify(url) if url else f"capture-{now_iso()[:10]}"
            if fallback_slug in existing_slugs:
                fallback_slug = f"{fallback_slug}-{now_iso()[:10]}"
            create_thread(fallback_slug, title or fallback_slug)
            append_entry(fallback_slug, title, url, body)
            filed_to.append(fallback_slug)
            created_new.append(fallback_slug)

    regenerate_index()

    thread_list = ", ".join(filed_to)
    new_badge = f" (new: {', '.join(created_new)})" if created_new else ""
    return {
        "ok": True,
        "threads": filed_to,
        "created_new": created_new,
        "thread": filed_to[0] if filed_to else "",  # backward compat
        "message": f"Captured to {thread_list}{new_badge}",
    }


# ---------- Main ----------

def main():
    try:
        msg = read_message()
        if msg is None:
            return
        op = msg.get("op")
        if op == "list-threads":
            send_message(handle_list_threads())
        elif op == "capture":
            send_message(handle_capture(msg))
        elif op == "ask":
            send_message(handle_ask(msg))
        elif op == "ping":
            cfg = load_config()
            send_message({
                "ok": True,
                "vault": str(VIBENOTE_HOME),
                "claude_config_dir": expand_path(cfg["claude_config_dir"]),
            })
        else:
            send_message({"ok": False, "error": f"Unknown op: {op}"})
    except Exception as e:
        # Send error back to extension and log to stderr (Chrome captures it).
        try:
            send_message({"ok": False, "error": f"{type(e).__name__}: {e}"})
        except Exception:
            pass
        print(f"vibenote-bridge error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
