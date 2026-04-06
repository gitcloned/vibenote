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
CONCEPTS_DIR = VIBENOTE_HOME / "concepts"
INDEX_PATH = VIBENOTE_HOME / "meta" / "index.md"
USAGE_LOG_PATH = VIBENOTE_HOME / "meta" / "usage.log"
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


def log_usage(op, **kwargs):
    """Append a one-line entry to the usage log. Fire-and-forget — never fails the caller."""
    try:
        parts = [f"{now_iso()} op={op}"]
        for k, v in kwargs.items():
            if v is not None:
                parts.append(f"{k}={v}")
        line = " ".join(parts) + "\n"
        USAGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(USAGE_LOG_PATH, "a") as f:
            f.write(line)
    except Exception:
        pass  # never let logging break the operation


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

def compute_strength(concept, notes):
    """
    Compute concept strength using recency-weighted substantiveness.
    strength = Σ substantiveness(thread) × e^(-0.03 × days_since_updated)
    """
    import math
    now_epoch = time.time()
    total = 0.0
    subs = concept.get("substantiveness", {})
    for note in notes:
        slug = note["slug"]
        if slug not in [t for t in concept.get("threads", [])]:
            continue
        # Get the thread's updated timestamp from its file
        thread_file = THREADS_DIR / f"{slug}.md"
        days = 0
        if thread_file.exists():
            for line in thread_file.read_text().splitlines():
                if line.startswith("updated:"):
                    ts_str = line.split(":", 1)[1].strip()
                    try:
                        from datetime import datetime as dt
                        updated = dt.fromisoformat(ts_str.replace("Z", "+00:00"))
                        days = (datetime.now(timezone.utc) - updated).days
                    except Exception:
                        pass
                    break
        sub_score = float(subs.get(slug, 0.5))
        decay = math.exp(-0.03 * days)
        total += sub_score * decay
    return round(total, 3)


def run_claude(prompt, claude_bin, claude_dir, timeout=45):
    """Run claude -p and return the raw text output. Returns None on any error."""
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
            print(f"vibenote-bridge: claude error (rc={result.returncode}): {result.stderr[:200]}", file=sys.stderr)
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("vibenote-bridge: claude timed out", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("vibenote-bridge: claude binary not found", file=sys.stderr)
        return None


def parse_json_from_llm(raw):
    """Parse JSON from LLM output, stripping markdown code fences if present."""
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"vibenote-bridge: JSON parse error: {e}", file=sys.stderr)
        return None


def extract_concepts(notes, claude_bin, claude_dir, timeout=60):
    """
    Use the LLM to identify concepts that span 2+ threads.
    Returns a list of concept dicts: [{slug, description, threads, substantiveness}]
    """
    notes_block = "\n\n".join(
        f"=== {n['slug']} ===\n{n['structured_note']}"
        for n in notes
    )

    prompt = f"""You are analyzing a personal knowledge base to find concepts that span multiple threads. A "concept" is an idea, framework, technique, or theme that appears meaningfully in 2 or more threads.

Rules:
1. Only extract concepts that appear SUBSTANTIVELY in 2+ threads — not just keyword overlap.
2. Each concept should be atomic (one idea per concept, not a category).
3. For each concept, rate substantiveness per thread: 1.0 = core topic, 0.5 = discussed significantly, 0.3 = mentioned but not central.
4. Generate a slug (lowercase, hyphenated), a one-sentence description, and list which threads reference it.
5. Aim for quality over quantity — 3 genuine cross-thread concepts are better than 10 superficial ones.
6. Look for non-obvious connections — concepts that the user might not realize connect their threads.

THREADS:

{notes_block}

Return ONLY a valid JSON array (no markdown fences, no explanation):
[
  {{
    "slug": "concept-slug",
    "title": "Concept Title",
    "description": "One-sentence description of what this concept is",
    "threads": ["thread-slug-1", "thread-slug-2"],
    "substantiveness": {{"thread-slug-1": 1.0, "thread-slug-2": 0.5}},
    "connections_insight": "One sentence about what's interesting about how this concept appears differently across the threads"
  }}
]"""

    raw = run_claude(prompt, claude_bin, claude_dir, timeout)
    data = parse_json_from_llm(raw)
    if not isinstance(data, list):
        return []

    # Validate: only keep concepts with 2+ threads that actually exist
    existing_slugs = {n["slug"] for n in notes}
    valid = []
    for c in data:
        if not isinstance(c, dict):
            continue
        threads = [t for t in c.get("threads", []) if t in existing_slugs]
        if len(threads) < 2:
            continue
        c["threads"] = threads
        valid.append(c)
    return valid


def generate_concept_page(concept, notes, claude_bin, claude_dir, timeout=45, concepts_data_context=None):
    """
    Generate a full concept page for a single concept.
    Returns the markdown string to write to the concept file.
    concepts_data_context: the full list of extracted concepts (for strict linking).
    """
    slug = concept["slug"]
    title = concept.get("title", slug)
    description = concept.get("description", "")
    threads = concept.get("threads", [])
    substantiveness = concept.get("substantiveness", {})
    insight = concept.get("connections_insight", "")

    # Collect the relevant structured notes
    relevant_notes = "\n\n".join(
        f"=== {n['slug']} ===\n{n['structured_note']}"
        for n in notes if n["slug"] in threads
    )

    # Build a list of existing concept slugs so the Connections section only links to real pages.
    existing_concepts = [
        c.get("slug") for c in concepts_data_context
        if c.get("slug") and c.get("slug") != slug
    ] if concepts_data_context else []
    existing_concepts_hint = ", ".join(existing_concepts) if existing_concepts else "(none yet)"

    # Build journal entry references so the LLM can cite specific entries.
    journal_refs = []
    for n in notes:
        if n["slug"] not in threads:
            continue
        thread_file = THREADS_DIR / f"{n['slug']}.md"
        if not thread_file.exists():
            continue
        text = thread_file.read_text()
        # Extract journal entry timestamps and first ~100 chars of each
        in_journal = False
        current_ts = None
        current_preview = []
        for line in text.splitlines():
            if line.startswith("## Journal"):
                in_journal = True
                continue
            if in_journal and line.startswith("### "):
                if current_ts and current_preview:
                    preview = " ".join(current_preview)[:150]
                    journal_refs.append(f"- {n['slug']}, {current_ts[:10]}: {preview}")
                current_ts = line[4:].strip()
                current_preview = []
            elif in_journal and current_ts and line.strip() and not line.startswith("**Source:"):
                current_preview.append(line.strip())
        if current_ts and current_preview:
            preview = " ".join(current_preview)[:150]
            journal_refs.append(f"- {n['slug']}, {current_ts[:10]}: {preview}")

    journal_refs_block = "\n".join(journal_refs) if journal_refs else "(no journal entries available)"

    prompt = f"""You are writing a concept page for someone's personal knowledge base. This concept connects multiple threads of their thinking. Your job: synthesize what they know into a page that sounds like it was written by a sharp, thoughtful friend — not an AI assistant.

PERSONA: You're a friend who's been reading all their notes and just noticed something they missed. You think out loud. You make direct connections without hedging. You use "you" and "your." You don't say "both domains converge" — you say "this is the same problem showing up in two places." You're concise and opinionated. No filler, no academic framing, no "it appears that."

CONCEPT: {title}
DESCRIPTION: {description}
APPEARS IN: {', '.join(threads)}
CONNECTION INSIGHT: {insight}

RELEVANT THREAD NOTES:

{relevant_notes}

JOURNAL ENTRIES (cite specific entries using the format "(thread-slug, YYYY-MM-DD)"):

{journal_refs_block}

OTHER CONCEPTS THAT EXIST (only link to these — don't invent wikilinks to concepts that don't exist):
{existing_concepts_hint}

Write the concept page body with these sections (markdown, no frontmatter):

## What I know
3-5 paragraphs synthesizing what YOU (the user) understand about this concept across your threads. Not a thread-by-thread summary — a genuine synthesis that generates connections neither thread makes alone. Write conversationally. Cite specific journal entries inline as (thread-slug, YYYY-MM-DD). Make bold connections. Say "this is basically the same thing as" when it is.

## Where it appears
For each thread, 1-2 sentences about what angle that thread takes on this concept.

## Open questions
Questions that only become visible when you see this concept from multiple angles. Frame them as things the user might actually want to investigate next.

## Connections
ONLY link to concepts from this list: {existing_concepts_hint}. Format: [[slug|Display Name]]. If no existing concepts relate, write "No linked concepts yet — this will grow as your vault grows." Do NOT invent wikilinks to concepts that don't exist.

## Sources
List the specific journal entries this page draws from. Format:
- thread-slug, YYYY-MM-DD — one-line summary of what that entry contributes"""

    raw = run_claude(prompt, claude_bin, claude_dir, timeout)
    if not raw:
        return None

    # Compute strength
    strength = compute_strength(concept, notes)

    # Build the full page with frontmatter
    threads_yaml = "\n".join(f"  - {t}" for t in threads)
    subs_yaml = "\n".join(f"  {t}: {substantiveness.get(t, 0.5)}" for t in threads)

    page = f"""---
slug: {slug}
type: concept
description: {description}
threads:
{threads_yaml}
strength: {strength}
substantiveness:
{subs_yaml}
first_seen: {now_iso()}
last_updated: {now_iso()}
last_accessed: null
state: active
---

# {title}

{raw}
"""
    return page


def generate_concept_index():
    """Generate concepts/index.md from all active concept pages."""
    if not CONCEPTS_DIR.exists():
        return

    lines = ["# Vibenote Concept Index", "", "| concept | description | threads | strength | state |",
             "|---------|-------------|---------|----------|-------|"]

    for f in sorted(CONCEPTS_DIR.glob("*.md")):
        if f.name == "index.md":
            continue
        text = f.read_text()
        meta = {}
        in_fm = False
        for line in text.splitlines():
            if line.strip() == "---":
                if in_fm:
                    break
                in_fm = True
                continue
            if in_fm and ":" in line and not line.startswith("  "):
                key, _, val = line.partition(":")
                meta[key.strip()] = val.strip()

        slug = meta.get("slug", f.stem)
        desc = meta.get("description", "")
        if len(desc) > 80:
            desc = desc[:77] + "..."
        strength = meta.get("strength", "0")
        state = meta.get("state", "active")
        # Count threads from YAML list
        thread_count = sum(1 for l in text.splitlines() if l.strip().startswith("- ") and l.strip()[2:].replace("-", "").isalpha())

        lines.append(f"| [[{slug}]] | {desc} | {thread_count} | {strength} | {state} |")

    (CONCEPTS_DIR / "index.md").write_text("\n".join(lines) + "\n")


def insert_wikilinks(concepts_data):
    """
    Insert [[concept]] wikilinks into structured notes where concepts are mentioned.
    Only modifies the Structured Note section — never touches My Notes or Journal.
    """
    if not concepts_data:
        return

    for f in sorted(THREADS_DIR.glob("*.md")):
        slug = f.stem
        text = f.read_text()

        # Find which concepts reference this thread
        relevant_concepts = [
            c for c in concepts_data
            if slug in c.get("threads", [])
        ]
        if not relevant_concepts:
            continue

        # Extract the structured note section
        lines = text.splitlines()
        sn_start = None
        sn_end = None
        for i, line in enumerate(lines):
            if line.startswith("## Structured Note"):
                sn_start = i
            elif sn_start is not None and line.startswith("## ") and i > sn_start:
                sn_end = i
                break
        if sn_start is None:
            continue
        if sn_end is None:
            sn_end = len(lines)

        # Get the structured note text
        sn_text = "\n".join(lines[sn_start:sn_end])

        # Insert wikilinks — replace the concept title/slug with [[slug|Title]]
        # Only do this if the link doesn't already exist
        modified = False
        for concept in relevant_concepts:
            c_slug = concept["slug"]
            c_title = concept.get("title", c_slug)
            wikilink = f"[[{c_slug}|{c_title}]]"

            # Skip if already linked
            if f"[[{c_slug}" in sn_text:
                continue

            # Try to find the concept title or slug in the text and wrap it
            # Be careful: only replace the first occurrence, and only in running text
            # (not in headings or frontmatter-like lines)
            for target in [c_title, c_slug.replace("-", " ").title(), c_slug]:
                if target in sn_text and f"[[{c_slug}" not in sn_text:
                    # Replace first occurrence only
                    sn_text = sn_text.replace(target, wikilink, 1)
                    modified = True
                    break

            # If no text match found, append a reference line at the end of the section
            if f"[[{c_slug}" not in sn_text:
                sn_text = sn_text.rstrip() + f"\n\n*Related concepts: {wikilink}*"
                modified = True

        if modified:
            # Reconstruct the file with the modified structured note
            new_lines = lines[:sn_start] + sn_text.splitlines() + lines[sn_end:]
            f.write_text("\n".join(new_lines))


def handle_read_concept(payload):
    """Read a concept page and return its parsed content."""
    slug = (payload.get("slug") or "").strip()
    if not slug:
        return {"ok": False, "error": "No concept slug provided."}

    path = CONCEPTS_DIR / f"{slug}.md"
    if not path.exists():
        return {"ok": False, "error": f"Concept not found: {slug}"}

    text = path.read_text()

    # Parse frontmatter
    meta = {}
    in_fm = False
    fm_end = 0
    for i, line in enumerate(text.splitlines()):
        if line.strip() == "---":
            if in_fm:
                fm_end = i + 1
                break
            in_fm = True
            continue
        if in_fm and ":" in line and not line.startswith("  "):
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()

    # Extract the body (everything after frontmatter)
    body_lines = text.splitlines()[fm_end:]
    body = "\n".join(body_lines).strip()

    # Update last_accessed
    ts = now_iso()
    updated_text = re.sub(r"^last_accessed:.*$", f"last_accessed: {ts}", text, count=1, flags=re.MULTILINE)
    if updated_text != text:
        path.write_text(updated_text)

    return {
        "ok": True,
        "slug": slug,
        "description": meta.get("description", ""),
        "strength": float(meta.get("strength", "0")),
        "state": meta.get("state", "active"),
        "body": body,
    }


def handle_list_threads():
    return {"ok": True, "threads": read_index()}


def handle_list_concepts():
    """Return the list of active concept pages from the concepts directory."""
    concepts = []
    if not CONCEPTS_DIR.exists():
        return {"ok": True, "concepts": concepts}
    for f in sorted(CONCEPTS_DIR.glob("*.md")):
        if f.name == "index.md":
            continue
        text = f.read_text()
        meta = {}
        for line in text.splitlines():
            if line == "---":
                if meta:
                    break
                continue
            if ":" in line:
                key, _, val = line.partition(":")
                meta[key.strip()] = val.strip()
        concepts.append({
            "slug": meta.get("slug", f.stem),
            "description": meta.get("description", ""),
            "strength": float(meta.get("strength", "0")),
            "state": meta.get("state", "active"),
            "threads": [t.strip() for t in meta.get("threads", "").strip("[]").split(",") if t.strip()],
        })
    return {"ok": True, "concepts": concepts}


def handle_process_concepts(payload):
    """
    Extract concepts from all structured notes and generate/update concept pages.
    This is the core cross-references engine.
    """
    config = load_config()
    claude_dir = expand_path(config["claude_config_dir"])
    timeout = config["ask"]["timeout_seconds"]

    claude_bin = find_claude_binary()
    if not claude_bin:
        return {"ok": False, "error": "claude CLI not found."}

    # Step 1: Load all structured notes
    notes = load_all_structured_notes()
    if len(notes) < 2:
        return {
            "ok": True,
            "message": "Need at least 2 threads with structured notes for concept extraction.",
            "concepts_generated": 0,
            "concepts_updated": 0,
        }

    # Step 2: Extract concepts via LLM
    concepts_data = extract_concepts(notes, claude_bin, claude_dir, timeout)
    if not concepts_data:
        return {
            "ok": True,
            "message": "No cross-thread concepts found.",
            "concepts_generated": 0,
            "concepts_updated": 0,
        }

    # Step 3: Generate concept pages (use a longer timeout — page generation
    # involves richer prompts with journal refs and persona instructions)
    page_timeout = max(timeout, 90)
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    generated = 0
    updated = 0
    for concept in concepts_data:
        slug = concept.get("slug", "")
        if not slug:
            continue
        page_path = CONCEPTS_DIR / f"{slug}.md"
        is_new = not page_path.exists()

        # Generate the full concept page via LLM
        page_content = generate_concept_page(
            concept, notes, claude_bin, claude_dir, page_timeout,
            concepts_data_context=concepts_data,
        )
        if page_content:
            page_path.write_text(page_content)
            if is_new:
                generated += 1
            else:
                updated += 1

    # Step 4: Generate concept index
    generate_concept_index()

    # Step 5: Insert wikilinks into structured notes
    insert_wikilinks(concepts_data)

    regenerate_index()

    return {
        "ok": True,
        "message": f"Processed {len(concepts_data)} concepts ({generated} new, {updated} updated).",
        "concepts_generated": generated,
        "concepts_updated": updated,
        "concepts": [c.get("slug") for c in concepts_data],
    }


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

    t0 = time.time()
    answer = run_claude(prompt, claude_bin, claude_dir, timeout)
    elapsed_ms = int((time.time() - t0) * 1000)

    if not answer:
        return {
            "ok": False,
            "error": "claude returned no response. Check that Claude Code is running and authenticated.",
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
        t0 = time.time()

        if op == "list-threads":
            result = handle_list_threads()
            log_usage(op, thread_count=len(result.get("threads", [])))
            send_message(result)
        elif op == "capture":
            result = handle_capture(msg)
            threads = ",".join(result.get("threads", []))
            log_usage(op, threads=threads or result.get("thread"),
                      latency_ms=int((time.time() - t0) * 1000))
            send_message(result)
        elif op == "ask":
            result = handle_ask(msg)
            scope = msg.get("thread") or "all"
            log_usage(op, scope=f"thread:{scope}" if msg.get("thread") else "all",
                      latency_ms=result.get("latency_ms"),
                      cited=",".join(result.get("cited_slugs", [])))
            send_message(result)
        elif op == "list-concepts":
            result = handle_list_concepts()
            log_usage(op, concept_count=len(result.get("concepts", [])))
            send_message(result)
        elif op == "read-concept":
            result = handle_read_concept(msg)
            log_usage(op, scope=f"concept:{msg.get('slug', '')}")
            send_message(result)
        elif op == "process-concepts":
            result = handle_process_concepts(msg)
            log_usage(op, latency_ms=int((time.time() - t0) * 1000),
                      generated=result.get("concepts_generated"),
                      updated=result.get("concepts_updated"))
            send_message(result)
        elif op == "ping":
            cfg = load_config()
            log_usage(op)
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
