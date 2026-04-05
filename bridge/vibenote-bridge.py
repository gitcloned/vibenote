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
from datetime import datetime, timezone
from pathlib import Path

VIBENOTE_HOME = Path(os.environ.get("VIBENOTE_HOME", Path.home() / ".vibenote"))
THREADS_DIR = VIBENOTE_HOME / "threads"
INDEX_PATH = VIBENOTE_HOME / "meta" / "index.md"
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
            # Header row uses text labels, not slugs — skip it if encountered.
            if not parts or parts[0] in ("slug", ""):
                continue
            # Expected columns: slug, state, updated, entries, processed, summary
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
                # Older index format fallback.
                threads.append({
                    "slug": parts[0],
                    "state": parts[1],
                    "updated": parts[2],
                    "entries": "",
                    "processed": "",
                    "summary": parts[-1],
                })
    return threads


def auto_classify(title, url, threads):
    """
    Pick the best matching thread based on keyword overlap with thread
    slugs and summaries. Returns slug or None if no match.

    Scoring: +1 per keyword (>=4 chars) from the title that appears in the
    thread slug or summary (case-insensitive). Requires at least 1 match.
    """
    if not threads:
        return None

    # Tokenize the title, keeping only meaningful words.
    stopwords = {
        "this", "that", "with", "from", "have", "what", "when", "where",
        "which", "their", "about", "there", "would", "could", "should",
        "been", "were", "will", "your", "into", "some", "over", "than",
        "them", "then", "they", "than", "very", "also", "just", "more",
        "most", "other", "such", "only", "like", "between",
    }
    words = re.findall(r"\b[a-z]{4,}\b", title.lower())
    keywords = [w for w in words if w not in stopwords]

    best_slug = None
    best_score = 0
    for t in threads:
        haystack = f"{t['slug']} {t.get('summary', '')}".lower()
        score = sum(1 for kw in keywords if kw in haystack)
        if score > best_score:
            best_score = score
            best_slug = t["slug"]

    return best_slug if best_score > 0 else None


def thread_path(slug):
    return THREADS_DIR / f"{slug}.md"


def create_thread(slug, title):
    """Create a new thread file with the standard template."""
    ts = now_iso()
    content = f"""---
slug: {slug}
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


def handle_capture(payload):
    title = (payload.get("title") or "").strip()
    url = (payload.get("url") or "").strip()
    body = (payload.get("content") or "").strip()
    requested_thread = (payload.get("thread") or "").strip()

    # Empty body is allowed — this is "bookmark mode" where the user clicks
    # Capture without typing anything. The resulting entry is just the source
    # line (title + URL). Must still have a title or URL to identify what
    # we're bookmarking though.
    if not body and not title and not url:
        return {"ok": False, "error": "Nothing to capture — no title, URL, or content."}

    threads = read_index()
    existing_slugs = {t["slug"] for t in threads}

    if requested_thread:
        slug = requested_thread
        created_new = slug not in existing_slugs
    else:
        matched = auto_classify(title, url, threads)
        if matched:
            slug = matched
            created_new = False
        else:
            slug = slugify(title) if title else slugify(url) or f"capture-{now_iso()[:10]}"
            # Avoid collision with existing slugs.
            if slug in existing_slugs:
                slug = f"{slug}-{now_iso()[:10]}"
            created_new = True

    if created_new:
        create_thread(slug, title or slug)

    append_entry(slug, title, url, body)
    regenerate_index()

    return {
        "ok": True,
        "thread": slug,
        "created_new": created_new,
        "message": f"Captured to {slug}" + (" (new thread)" if created_new else ""),
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
        elif op == "ping":
            send_message({"ok": True, "vault": str(VIBENOTE_HOME)})
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
