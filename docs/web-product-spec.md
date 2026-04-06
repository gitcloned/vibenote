# Vibenote Web — Product Spec

> A dashboard for your second brain. Ask, reflect, navigate — without leaving the browser and without touching the raw files.

## 1. Why this exists

Vibenote today has three surfaces, each good at its primary job:

| Surface | Primary job |
|---|---|
| Chrome extension | Capture ingress from reading |
| Claude Code | Deep conversation, synthesis, long-form Q&A |
| Obsidian | Manual browse, raw editing, graph view |

None of them give the user a place to **stand back and see their thinking as a whole**. Specifically, these jobs have no good home today:

- **Morning review** — "what was I working on, what's unresolved, what moved yesterday"
- **Weekly reflection** — "what did I learn, what's stale, where am I stuck"
- **Live reference during a meeting** — "pull up what I know about X right now"
- **Sharing a brief** — "send this topic as a standalone doc to a colleague"
- **At-a-glance state** — "show me all my open questions across every thread"

These require a surface that is calm, macro-level, quick to open, and primarily for *reflection* — not capture, not editing, not conversation. That's what the web product is.

**The one sentence:** *Vibenote Web is where you go to ask your second brain.*

## 2. Story — Sarah's Sunday morning

Sarah has been capturing into Vibenote for three weeks. Most days, 5–10 captures from tweets, articles, conversations, product ideas. She hasn't looked back at most of them.

Sunday morning, coffee in hand, she opens `vibenote.local` in her browser. The page loads in under a second.

At the top of the page is a question box with her cursor already inside. Placeholder text: *"What do you want to know?"* Below the box, three quiet buttons: **What did I learn this week?** · **What are my open questions?** · **What should I work on next?**

She clicks the first. Ten seconds later, the page fills with a weekly brief, synthesized from her captures:

- Seven things she learned, grouped by topic, each with citations back to the source threads
- Three decisions she made, with one-line reasoning
- Two commitments she made to herself that she hasn't acted on

She scrolls down. A "this week" card summarizes: *11 new captures · 1 new thread · 5 open questions*.

Below that, every thread she has is a small card, sorted by most recent activity. Active threads are full-colored; stale ones (no captures in 14+ days) are dimmed. She notices `auth-rewrite` is dim — hasn't moved in 10 days. She clicks it. The structured note expands inline. She reads it, remembers where she was stuck (waiting on a compliance doc from legal), clicks *"Ask about this thread"*, types "what am I blocked on?", reads the answer, and makes a mental note to chase legal on Monday.

Five minutes, she closes the tab. Her week feels planned, not reactive. Sunday-at-Vibenote becomes a ritual.

## 3. Design principles

These govern every decision. In priority order, so conflicts resolve top-down.

**1. One primary action.** The ask box is the center of the page. Everything else is peripheral. If the user opens the tab and does nothing but ask a question and read the answer, they got the full value of the surface.

**2. Show, don't store.** The web product renders the local vault; it never stores new state. No accounts, no sync, no cloud. The vault on disk remains the single source of truth. Every page view is a read.

**3. Context over content.** Default views show synthesized structured notes and LLM-generated answers — not raw journal dumps. Raw content is still reachable but one layer deeper. The first thing the user sees is *meaning*, not *data*.

**4. Time as a first-class dimension.** The human brain anchors memory to time. Every view is filtered or colored by when: this week, today, stale, recent. "When" is as important as "what."

**5. Citations everywhere.** Every claim in every answer links back to a specific thread. Every card has a source. The user can always trace a synthesis to its raw material. Trust is earned through traceability.

**6. No configuration before value.** First visit loads the dashboard. No login, no tour, no wizard, no settings gate. The product works out of the box with the existing vault. Configuration, if any, happens inline and only for users who need to override the defaults.

**7. Reflection, not action.** The web product is for thinking *about* your thinking. Capture happens in the extension or Claude Code; new work happens in your editor. The web surface is a quiet review space that does *not* compete with those.

**8. Calm by default.** No notifications, no unread badges, no "come back" nudges, no streaks, no gamification. The user opens the tab when they want to — not because the product pulled them. Being pulled is what every other tool in their life does; Vibenote should feel restorative.

## 4. The primary action — the ask box

Everything about the ask box is designed to minimize time-from-question-to-answer.

- **Auto-focused on page load.** First keystroke types into the question, no click needed.
- **Adaptive placeholder text.** Shows a different example depending on vault state:
  - Default: *"What do you want to know?"*
  - After recent research captures: *"Why did I pick GRPO?"*
  - When many open questions exist: *"What are my open questions?"*
  - Fresh vault: *"Capture something first, then come ask."*
- **Three shortcut buttons.** Preset queries that cover 80% of real use:
  1. *What did I learn this week?*
  2. *What are my open questions?*
  3. *What should I work on next?*
- **Answer appears inline below the box.** No navigation, no page reload. Clear loading state (~10s is normal latency because of the Claude CLI subprocess).
- **Citations are clickable.** Each `(from <slug>)` in the answer becomes a link that expands that thread's structured note inline. Clicking an expanded thread's citation opens the file in Obsidian as the deeper navigation path.
- **Follow-up is NOT supported in V1.** Each question is independent. Users re-ask if they need to go deeper. Adding conversation state is V2 scope.

## 5. Information architecture

Single page. Three zones, stacked vertically. No nav bar, no sidebar, no multiple routes.

**Zone 1 — Ask (top, hero).** Question box, three shortcut buttons, answer render area. Always above the fold.

**Zone 2 — This week.** One card showing: new captures count, new threads count, open questions count, a tiny sparkline of daily capture activity. A glance-level snapshot. Visible without scrolling on desktop.

**Zone 3 — Threads.** Every thread as a card in a responsive grid. Each card shows: slug, one-line summary (extracted from structured note), last updated, entry count, state pill (*active* / *stale* / *sparking*). Click a card to expand the full structured note inline. Each expanded card has an *"Ask about this thread"* button that pre-fills the question box with a thread-scoped query.

**Footer.** Subtle. Just the vault path, Vibenote version, and the current Claude config dir (so power users can verify which environment is active).

## 6. V1 scope

**In:**
- Ask box with free-form query
- Three shortcut query buttons
- Answer rendering with clickable citations
- This-week summary card
- Threads grid with inline expansion
- "Ask about this thread" button on expanded threads
- "Copy markdown brief" button on each thread (for sharing — just a clipboard copy, not a public link)
- Current config dir visible in footer
- Dark mode (system preference)
- Loading / error states for every async call

**Out (explicit):**
- Authentication or user accounts
- Cloud sync or backup
- Public sharing links with URLs
- Mobile-optimized layout (desktop only for V1)
- Editing or deleting thread content
- Full-text search (Obsidian handles this)
- Graph view (Obsidian handles this)
- Teams, collaboration, multi-user
- Follow-up questions / conversation context
- Answer history
- Settings UI (config file edits are enough)
- Onboarding tour
- Notifications of any kind

## 7. Technical architecture

Local-first, consistent with the rest of Vibenote.

```
Browser (static HTML/CSS/JS at http://localhost:3137/)
    ↓ fetch
vibenote-bridge.py --serve   (new HTTP server mode)
    ↓ reads
~/.vibenote/threads/*.md   ~/.vibenote/meta/index.md
    ↓ subprocess: claude -p (for ask queries)
Claude Code via user's existing auth
```

**The server is the same bridge binary** we already use for the Chrome extension, just in a second mode (`--serve` flag). This keeps the surface area small and the installation model unchanged.

### Endpoints (HTTP, localhost only)

- `GET /` → serves the static web UI (HTML/CSS/JS bundle)
- `GET /api/index` → returns parsed thread index
- `GET /api/thread/<slug>` → returns `{frontmatter, structured_note, my_notes, journal_entries[]}` (My Notes included here because it's the user's own content, but rendered read-only)
- `GET /api/week` → returns this-week summary `{captures, threads, open_questions, daily_counts[]}`
- `POST /api/ask` → takes `{question}`, runs `claude -p` via subprocess with structured notes as context, returns `{answer, latency_ms, cited_slugs[]}`
- `POST /api/query/<type>` → pre-baked queries: `open-questions`, `recent-activity`, `recent-decisions`, `stale-threads`

### Static bundle

Plain HTML/CSS/JS. No framework. No build step. Ships as part of the plugin install under `~/.vibenote/web/`. Total bundle size target: under 100 KB uncompressed. Loads in under 1 second.

### Server lifecycle and entry point

V1 ships a single command — **`vibenote-server`** — that handles the entire lifecycle. Installed as a shell script at `~/.vibenote/bin/vibenote-server` and symlinked into the user's PATH (or appended to their shell profile) by `install.sh`.

The command has three modes, auto-detected based on current state:

1. **Not running → start and open.** If no server is running, spawn the bridge in `--serve` mode as a detached background process, wait for it to accept connections, then `open http://localhost:3137/` in the default browser. User sees the browser tab appear; nothing else.
2. **Already running → just open.** If the server is already running (detected via PID file at `~/.vibenote/meta/server.pid` + a health check on `/api/health`), skip the start, just open the browser. Idempotent — the user can run it as many times as they want.
3. **`--stop` flag → stop.** Graceful SIGTERM to the server, remove the PID file, remove `~/.vibenote/meta/server.json`.

Also exposed as a **natural-language trigger in the Claude Code skill**: *"Hey Vibenote, open the web"* invokes the same script via the skill's `On serve` intent. Both entry points call the same underlying script — one implementation, two surfaces.

**State files** under `~/.vibenote/meta/`:
- `server.pid` — the detached server's process ID (for stop and health check)
- `server.json` — `{port, pid, started_at}` so other tools and the Claude Code skill can introspect state

The user never types a URL. The URL is an implementation detail the command handles on their behalf.

### Port selection

Default: `3137` (deliberate — four digits, unlikely to collide with common dev ports).

If 3137 is in use: the server tries 3138, 3139, … up to 3147. The actual port gets written to `~/.vibenote/meta/server.json` so `vibenote-server` knows which URL to open on subsequent invocations.

### Why not a pretty URL like `vibenote.local`

An earlier draft proposed adding a `/etc/hosts` entry so users could type `vibenote.local` instead of `localhost:3137`. We considered it and rejected it for V1 for four reasons:

1. **`.local` is reserved for mDNS / Bonjour.** On macOS especially, `.local` lookups are intercepted by mDNSResponder and may bypass `/etc/hosts` entirely, causing silent failures that are hard to debug.
2. **Modifying `/etc/hosts` requires sudo.** Breaks the `curl | sh` one-shot install. Uninstall has to remember to clean up.
3. **The port stays in the URL regardless** (unless we bind to port 80, which needs root every start). `vibenote.local:3137` vs `localhost:3137` is a marginal cosmetic improvement.
4. **The command opens the browser for the user.** Memorability of the URL doesn't matter if the user never types it.

If pretty URLs turn out to matter in practice, **V2 adds it as an opt-in feature** via `vibenote-server --install-hostname`, and uses **`vibenote.test`** (IETF-reserved, no mDNS conflicts, no HTTPS enforcement) — **not** `.local` and **not** `.dev`.

### Config dir integration

The server reads `~/.vibenote/config.json` (same file as the ask flow for the Chrome extension) to decide which `CLAUDE_CONFIG_DIR` to use for subprocess calls. Same source of truth. Same override path. Consistent across all surfaces.

## 8. Activation moments

The web product has its own activation journey, separate from the capture side:

**Activation 1 — First visit.** User opens `http://localhost:3137/` for the first time and sees their own vault rendered. The moment they think *"oh, this is MY stuff, organized."*

> **Design implication:** even before the user asks anything, the page has to be self-evidently valuable. The this-week card and threads grid carry this weight. The ask box is the primary action, but it's not the *only* thing that matters on first visit — the user needs to see concrete, personalized content immediately.

**Activation 2 — First successful query.** User types a question, gets a synthesized answer with citations. The moment they think *"this is actually my second brain."*

> **Design implication:** latency and answer quality are both critical here. A 30-second query with a mediocre answer kills this activation permanently. 10 seconds with a good answer earns retention.

**Activation 3 — First unprompted return.** User opens the tab on a Sunday or Monday morning without being told to. The ritual is forming. The moment the tool becomes part of their routine.

> **Design implication:** the product has to earn retention through value, not notifications. If Sarah forgets Vibenote exists, it lost. The only lever we have is making the first two activations so valuable she comes back on her own.

## 9. What we will not build (ever, probably)

Some features look attractive but betray the thesis of the product. They are rejected up front so we don't argue about them every release:

- **User accounts.** Local vault, no accounts, ever. Accounts add auth, privacy liability, migration complexity, and pressure to build cloud sync.
- **Cloud sync.** Break local-first. Pressure to build infrastructure. Compliance exposure.
- **Collaboration features.** Vibenote is a personal thinking tool. Teams have other tools. Don't confuse the categories.
- **Gamification.** Streaks, badges, XP. These manufacture engagement at the cost of calm. Principle 8 forbids them.
- **Public feed / social features.** Not what a second brain is for. Full stop.
- **AI auto-capture.** Auto-scanning the user's browser history or emails to capture proactively. Violates user control and the "never pull the user" rule.

## 10. Open questions

Questions worth resolving before V1 ships but not blocking the spec:

1. **Auto-start on login?** V1 ships `vibenote-server` as a manual command. V1.1 candidate: LaunchAgent plist / systemd user service that runs the server on login so the user can navigate to `localhost:3137` at any time without invoking the command first. Decide after seeing real usage.
2. **Cross-device access.** For the Sarah-on-her-phone case, the server has to be reachable from other devices on the same network. Bind to `0.0.0.0` behind a LAN-only firewall? Cloudflare tunnel? Defer to V2.
3. **Offline state.** `claude -p` requires network. When offline, the ask box should disable with a clear message. The dashboard (this-week, threads) should still work because it's all local reads.
4. **Answer caching.** 10-second queries are fast but not instant. Hash the prompt + vault state, cache for 5 minutes server-side. Adds ~30 lines, meaningful UX win. Include in V1 if the cache key is easy to get right.
5. **Large vault performance.** At 100+ threads, loading every structured note into the ask prompt will blow the context window. V1 target: up to 50 threads. V2: retrieval layer that picks the most relevant N threads per question.
6. **Discovery.** How does the user know `vibenote-server` exists? Print the command in `install.sh` output, print it in the Chrome extension's empty Notes-tab state, mention it in the Claude Code skill welcome message. Make it impossible to miss once.
7. **Pretty URL.** Deferred to V2 as documented in section 7. Use `vibenote.test` via `/etc/hosts` with an explicit `--install-hostname` opt-in flag, not during the normal install flow.

## 11. Build sequence (when we get there)

Not this session's work, but worth sketching so the spec isn't purely aspirational.

**Phase 1 — Server mode.** Extend the bridge with `--serve` flag, HTTP endpoints for `/api/index`, `/api/thread`, `/api/ask`. Test with `curl` before any UI.

**Phase 2 — Static UI scaffold.** Single HTML page, three zones, ask box wired to `/api/ask`, threads grid rendering from `/api/index`. No dashboard polish yet.

**Phase 3 — Dashboard polish.** This-week card, state pills on threads, adaptive placeholders, dark mode, loading states, error states.

**Phase 4 — Sharing.** Copy-markdown-brief button on each thread. That's the whole "sharing" feature for V1.

**Phase 5 — Auto-start.** LaunchAgent plist for macOS. User runs `vibenote serve --install-autostart` and the server runs on login.

Phases 1 and 2 alone are a valuable MVP. Everything after is polish.

---

**Status:** Spec locked. Build is deferred until we finish the Chrome extension Q&A work (Notes tab with Claude CLI integration). This document is the north star for that next build.
