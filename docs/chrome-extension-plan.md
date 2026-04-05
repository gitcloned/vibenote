# Vibenote Chrome Extension — V1 Build Plan

## Why this exists

Most developer thinking worth capturing happens while reading — tweets, HN, papers, blog posts, docs, GitHub. Today, capturing any of that with Vibenote requires switching to Claude Code, pasting the URL and comment, and waiting. Each step is a context switch. The friction kills the habit.

A browser extension shrinks capture to **one icon click, zero context switches**. That matches where the reading actually happens.

## What V1 ships

One interaction: click the Vibenote icon → side panel slides in → type your comment / paste anything from the page → hit Save. One click to open, one click to save. The side panel stays open while you read, so copy-paste-while-reading works.

### Side panel UI

- **Page title** (editable, pre-filled from active tab)
- **URL** (read-only, truncated with hover tooltip)
- **Thread dropdown** — empty by default. Populated from `~/.vibenote/meta/index.md` via the native host. User can optionally pick a thread. If left empty, the bridge auto-classifies on save (simple keyword/domain heuristic), creating a new thread if nothing matches.
- **One textarea** (autofocus, auto-resize) — free-form. User types their comment and pastes anything they want.
- **Save button** (also `Cmd+Enter`)
- **Status line** — "Connected", "Saved ✓", or error messages

### What saving does

One save = one new journal entry appended to the selected (or auto-classified) thread. Format:

```markdown
### 2026-04-05T14:23:11Z
**Source:** [Page Title](https://example.com/...)

<whatever the user typed, verbatim>
```

No reformatting, no LLM processing. The vault's "store it exactly" rule applies.

## Architecture

```
Chrome extension (side panel UI)
    ↓  Chrome native messaging (JSON over stdio, 4-byte length prefix)
~/.vibenote/bin/vibenote-bridge.py    (~150 lines)
    ↓  direct file write
~/.vibenote/threads/<slug>.md
```

**No daemon. No cloud. No network.** The bridge is invoked per-message by Chrome, runs briefly, exits. Extension has `activeTab` permission only — never sees URLs unless you invoke it.

### Bridge operations

- **`list-threads`** — reads the index, returns `{threads: [{slug, summary, processed, updated}, ...]}`
- **`capture`** — input `{title, url, content, thread?}`. If `thread` provided, uses it. Else: keyword-match against index; if top score > 0 use best match; else create new thread with slug derived from title. Appends a properly-formatted journal entry, updates frontmatter (`updated`, `entry_count`), regenerates the index.

### File format guarantees

- Proper YAML frontmatter (`---` wrapped)
- Includes `## My Notes` section (inviolable, never touched)
- Matches the template in `skills/vibenote/SKILL.md` exactly
- Uses the same ISO-8601 UTC timestamp format as Claude Code captures

## What V1 does NOT ship

- Readability.js / page clipping — user pastes manually instead
- Selection-to-quote / floating "+" buttons
- Block composer — one textarea only
- Popup Q&A — ingestion only, querying stays in Claude Code
- Inline annotations on the page
- Live markdown preview
- Reclassify / edit-thread-after-save
- Browser action badge counts
- Settings page
- Multi-thread capture (one save = one thread)

Each is a legitimate V2 candidate. None belong in V1. The discipline: **the extension is an ingestion surface. Organization happens automatically. Querying happens in Claude Code or the CLI.**

## Install flow (two steps)

### Step 1 — CLI infrastructure

```bash
curl -fsSL install.vibenote.dev | sh
```

The updated `install.sh`:
1. Installs Claude Code plugin (existing)
2. Initializes `~/.vibenote/` vault (existing)
3. Mirrors helper scripts into `~/.vibenote/scripts/` (existing)
4. **New:** Copies `vibenote-bridge.py` to `~/.vibenote/bin/`
5. **New:** Registers native messaging host manifest at `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.vibenote.bridge.json` (macOS path; Linux TBD in V2)
6. **New:** Prints the extension install instructions

### Step 2 — Extension

During development (before Chrome Web Store submission):
1. Open `chrome://extensions`
2. Enable Developer Mode
3. Click "Load unpacked" → select the `extension/` folder in the repo
4. Copy the extension ID shown
5. Run `bash ~/.vibenote/scripts/vn-link-extension.sh <extension-id>` — this rewrites the native host manifest to allow that specific extension ID
6. Close/reopen Chrome (or just the extension)

After Web Store submission: steps 2–6 collapse into "install from Web Store." The stable extension ID becomes known in advance, so `install.sh` can set it directly — the link helper is unnecessary.

## File layout

```
vibenote/
├── bridge/
│   └── vibenote-bridge.py              # The native messaging host
├── extension/
│   ├── manifest.json                   # Manifest V3
│   ├── background.js                   # Service worker (opens side panel on icon click)
│   ├── sidepanel.html                  # UI shell
│   ├── sidepanel.js                    # UI logic + native messaging client
│   ├── sidepanel.css                   # Minimal styling
│   ├── icons/                          # Toolbar icons (add before Web Store submission)
│   └── README.md                       # Dev install steps
├── scripts/
│   └── vn-link-extension.sh            # Helper: rewrites native host manifest with dev ext ID
├── install.sh                          # Updated: installs bridge + native host
└── docs/
    └── chrome-extension-plan.md        # This file
```

## Build order

1. Plan doc (this file)
2. Bridge script — self-contained, testable from CLI by piping framed JSON
3. `install.sh` updates + link helper script
4. Extension scaffold — manifest + side panel HTML/JS/CSS, mocked data
5. Wire extension → bridge via native messaging
6. Extension README with dev install flow
7. End-to-end test: click icon on a real page, save, verify journal entry

## Risks / notes

- **Python on macOS** — preinstalled but slowly being deprecated. V1 uses `#!/usr/bin/env python3` and runs on stock macOS. If Apple removes it, rewrite bridge as Go/Rust binary (same interface, no impact on extension).
- **Concurrent writes** — if Claude Code and the extension write to the same thread simultaneously, possible corruption. Unlikely in V1 (user is typically in one surface at a time). Mitigate in V2 with temp-file + rename.
- **Auto-classification quality** — simple keyword matching will sometimes pick the wrong thread. Acceptable for V1 because the user can always pick explicitly. V2 could add a "move to thread" command.
- **Chrome Web Store review** — adds ~1 week for updates. Plan accordingly. Dev-load works immediately.
- **Windows/Linux** — V1 targets macOS only. Native host manifest paths differ per-OS. V2 extends installer.
