# Vibenote

> A second brain that captures your thinking ambiently and connects the dots automatically.

You have threads of thinking that keep getting lost. Connections that only surface weeks later. A sense that your notes should be working harder for you. Vibenote is the tool I wish existed for that — a personal knowledge base that captures everything you read, think, and research, then automatically finds the connections you missed.

I was researching MCTS alternatives for small language models. Separately, I was studying corrective feedback strategies for an AI voice tutor. It took me three weeks to realize they're the same problem — a PRM scoring every reasoning step causes reward hacking, just like a teacher correcting every sentence kills fluency. Both fields independently arrived at "back off and let the learner self-correct."

I didn't notice this. My notes did.

## Quick start

### Option 1: Paste this into Claude Code (recommended)

Open Claude Code and paste this prompt. Claude handles the install and walks you through first use.

> Install Vibenote — a personal knowledge base that captures my thinking and connects dots across threads: run **`curl -fsSL https://raw.githubusercontent.com/gitcloned/vibenote/main/install.sh | bash`** and then tell me what Vibenote is and how I can start using it. If the install output mentions next steps, explain them.

Zero terminal interaction for you. Claude Code runs the install, verifies it worked, and onboards you in the same conversation.

### Option 2: `curl | bash` from your terminal

```bash
curl -fsSL https://raw.githubusercontent.com/gitcloned/vibenote/main/install.sh | bash
```

The installer auto-detects Claude Code, Claude Desktop, and Chrome, and sets up whichever integrations you have. ~15 seconds.

### Option 3: Clone and install (for contributors)

```bash
git clone https://github.com/gitcloned/vibenote.git
cd vibenote
./install.sh
```

## What gets installed

The installer auto-detects what you have and sets up accordingly:

| Integration | Requires | What you get |
|---|---|---|
| **Claude Code skill** | Claude Code | `Hey Vibenote, ...` capture + `process` + `ask` intents |
| **Native messaging bridge** | None (always installed) | Powers the Chrome extension and CLI flows |
| **Chrome extension** | Chrome browser | Side panel for capture + chat-based Q&A |
| **MCP server** | Claude Desktop, VS Code, Cursor, etc. | Vibenote tools available in any MCP client |

After install you get a summary of what was configured and clear next steps. The installer is idempotent — safe to re-run any time.

## How it works — three-tier memory

Inspired by how the brain consolidates memory (hippocampus → neocortex), the Generative Agents paper, and Luhmann's Zettelkasten:

```
Journals (raw captures, verbatim, append-only)
    ↓ process
Structured Notes (per-thread synthesis)
    ↓ process-all
Concept Cards (cross-thread patterns)
```

**Journals** — everything you capture, stored exactly as given. Never edited by the system.

**Structured Notes** — LLM-generated syntheses of each thread. Written in a human voice with inline citations back to specific journal entries.

**Concept Cards** — compressed patterns that span 2+ threads. Not essays. Each card names the pattern, states one key tension, poses one open question, and links to the evidence. Maybe 10 lines.

The vault is plain markdown at `~/.vibenote/`. Open it in Obsidian and the wikilinks light up the graph automatically.

## Your first five minutes

### 1. Capture something

**From Claude Code:**
> Hey Vibenote, I just read an interesting article about reinforcement learning for language models. GRPO seems to be replacing MCTS.

Vibenote creates a thread, classifies the topic, and logs the entry verbatim.

**From the Chrome extension** (if installed):
- Open any article or page
- Click the Vibenote icon in the toolbar
- Type a quick thought, hit Capture

**From Claude Desktop** (if configured):
> Save to Vibenote: the key insight is that RL training can make small models develop self-correction without external search.

### 2. See what's in your vault

**From Claude Code:**
> Hey Vibenote, list my threads

**From Claude Desktop (via MCP):**
> What's in my Vibenote vault?

**From Obsidian:**
- Open `~/.vibenote/` as a vault
- Use graph view, search, or browse the files

### 3. Process your threads

After a few captures:
> Hey Vibenote, process all

The processor synthesizes a structured note per thread and extracts concepts that span multiple threads. First time takes ~1-2 minutes. After that, processing is incremental.

### 4. Ask your notes anything

**From the Chrome extension Notes tab:**
Pick a thread, use a quick query (Where am I / Open questions / Next steps) or type a free-form question. Answers come back in ~10 seconds with citations back to specific entries.

**From Claude Code or Claude Desktop:**
> Hey Vibenote, what are my open questions across all my threads?

### 5. Open Obsidian on the vault

Point Obsidian at `~/.vibenote/` (or any Markdown-aware editor). See your threads, concepts, and the wikilink graph that ties them together.

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌───────────────────┐
│  Capture        │      │  Synthesize      │      │  Query            │
│  ─────────      │      │  ──────────      │      │  ─────            │
│  Claude Code    │──┐   │  Claude CLI      │   ┌──│  Claude Code      │
│  Chrome Ext.    │──┤   │  (process flow)  │   ├──│  Chrome Notes tab │
│  MCP (Desktop,  │──┤   │                  │   ├──│  MCP (any client) │
│   VS Code, …)   │  │   │                  │   │  │  Obsidian (direct)│
└─────────────────┘  │   └──────────────────┘   │  └───────────────────┘
                     ▼                           │
                 ┌─────────────────────────┐    │
                 │  ~/.vibenote/ (vault)   │◀───┘
                 │  threads/   concepts/   │
                 │  meta/      config.json │
                 └─────────────────────────┘
```

**Bridge** (`~/.vibenote/bin/vibenote-bridge.py`) — the Python script that every surface talks to. Reads and writes the vault, invokes Claude CLI for synthesis and classification.

**MCP server** (`~/.vibenote/bin/vibenote-mcp.py`) — same operations exposed over the Model Context Protocol for Claude Desktop, VS Code, Cursor, etc.

**Local-first, always.** Plain Markdown, no cloud, no accounts, no vendor lock-in. `git push` is your backup. The vault will outlive any product.

## Project structure

```
vibenote/
├── install.sh                 # One-command installer
├── uninstall.sh               # Clean removal
├── VERSION                    # Current version
├── skills/
│   └── vibenote/SKILL.md      # Claude Code skill definition
├── bridge/
│   └── vibenote-bridge.py     # Native messaging + vault ops
├── mcp/
│   ├── vibenote-mcp.py        # MCP server
│   └── README.md              # MCP setup for Claude Desktop, VS Code, etc.
├── extension/
│   ├── manifest.json          # Chrome Manifest V3
│   ├── sidepanel.{html,css,js} # Side panel UI
│   └── README.md              # Extension dev install
├── scripts/
│   ├── setup.sh               # Initializes ~/.vibenote/
│   ├── vn-update-index.sh     # Regenerates the thread index
│   └── vn-link-extension.sh   # Links dev-loaded extension ID
├── docs/
│   ├── cross-references-design.md  # Concept extraction design + testing
│   ├── web-product-spec.md         # Future localhost web dashboard
│   ├── chrome-extension-plan.md    # Extension architecture
│   └── gist-vibenote.md            # Public-facing overview
└── tests/
    └── fixtures/              # Test fixtures for structural tests
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `VIBENOTE_HOME` | `~/.vibenote` | Vault location |
| `CLAUDE_CONFIG_DIR` | `~/.claude` | Claude Code config dir (override if you use a custom install) |
| `VIBENOTE_BRANCH` | `main` | Branch to install from (for `curl \| bash` remote installs) |

For power users who want a non-default Claude Code config (e.g., you use `~/.claude-personal`), edit `~/.vibenote/config.json` after install to set `claude_config_dir`.

## Uninstall

```bash
./uninstall.sh
```

Removes the Claude Code plugin, native messaging bridge, MCP server, Chrome native host manifest, and MCP entry from Claude Desktop config. **Your vault (threads, concepts, my notes) is preserved** — you have to delete it manually with `rm -rf ~/.vibenote` if you want it gone.

## Status

This is an active personal project. The core (capture, process, ask, concepts) is working and used daily. The roadmap includes:

- [ ] Chrome Web Store publication (currently dev-load only)
- [ ] Local web dashboard (design in `docs/web-product-spec.md`)
- [ ] Auto-processing on capture thresholds
- [ ] Concept fading and merging
- [ ] Voice capture (mobile)
- [ ] More MCP clients tested (VS Code, Cursor, Windsurf)

## License

MIT.

## Credits

- Inspired by [Andrej Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — the three-tier memory pattern
- Install flow and philosophy borrowed liberally from [gstack](https://github.com/garrytan/gstack) (particularly the "paste into Claude Code" quick-start)
- Concept strength scoring inspired by the [Generative Agents paper](https://arxiv.org/abs/2304.03442) and [MemoryBank](https://arxiv.org/abs/2305.10250)
- Zettelkasten principles via [Niklas Luhmann](https://en.wikipedia.org/wiki/Zettelkasten) and [Andy Matuschak's evergreen notes](https://notes.andymatuschak.org/Evergreen_notes)
