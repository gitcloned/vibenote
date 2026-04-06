# Building a Second Brain That Actually Connects Your Thinking

I've been researching MCTS alternatives for small language models. Separately, I've been studying corrective feedback strategies for an AI voice tutor I'm building for children. Two completely different threads of work.

It took me three weeks to realize they're the same problem.

A Process Reward Model that scores every reasoning step causes reward hacking — the model learns to game the rubric instead of actually reasoning. A teacher who corrects every sentence kills fluency — the student learns to wait for correction instead of self-correcting. Both fields independently arrived at the same fix: back off, evaluate at the outcome, trust the learner to develop internal correction.

I didn't notice this. My notes did.

I've been building a tool called **Vibenote** that captures everything I think, read, and research — then automatically finds connections I missed. Here's how it works and what I've learned.

## The three-tier memory architecture

Inspired by how the brain consolidates memory (hippocampus → neocortex), the Generative Agents paper from Stanford, and Luhmann's Zettelkasten. Three layers, each derived from the one below:

```
Journals (raw captures, verbatim, append-only)
    ↓ process
Structured Notes (per-thread synthesis)
    ↓ process-all
Concept Cards (cross-thread patterns)
```

**Journals** are the raw captures. Anything you dump in — a thought, a pasted article, a URL, a half-formed idea. Stored exactly as given. Never edited by the system.

**Structured Notes** are LLM-generated syntheses of each thread's journal entries. Not summaries — syntheses. "Here's what you know, what you've decided, what's open." Written in your voice, with citations back to specific journal entries.

**Concept Cards** are the magic layer. When the processor reads all structured notes across threads, it identifies ideas that appear meaningfully in 2+ threads and generates a compressed card for each:

```markdown
# Feedback and Reward Signals

Whether you're correcting a child's pronunciation or training a 1.5B-param
model, the core problem is identical: which signal do you send back, and does
it produce genuine improvement or just surface compliance? PRMs over-optimized
for their own blind spots until DeepSeek-R1 ditched them for ground-truth
verifiers, producing models that spontaneously self-correct. That's Swain's
Output Hypothesis playing out in silicon.

**Tension:** The easier feedback is to automate, the more likely it optimizes
for a proxy rather than the real target.

**Open:** Can you map the SLA feedback typology onto a reward-shaping spectrum
for your tutor model?

→ [[ai-education-research]] · [[slm-optimization-research]]
Sources: ai-education-research (2026-04-02) · slm-optimization-research (2026-04-04)
```

That's ~10 lines. Not an essay — a compressed pattern with links. The brain doesn't store essays about concepts. It stores patterns, key associations, and one sharp question. The concept card matches that.

## How capture works

Multiple ingestion surfaces, same vault:

**Claude Code** — the original surface. "Hey Vibenote, I think the auth rewrite should prioritize session storage" → logged instantly. Also handles deep Q&A, processing, and concept generation.

**Chrome Extension** — a side panel that stays open while you read. Click the icon on any page, type your thought (or paste from the page), hit Capture. The LLM classifies which thread(s) the capture belongs to — and yes, a single capture can go to multiple threads if it's relevant to more than one.

**Obsidian** — the vault is plain markdown at `~/.vibenote/`. Point Obsidian at it and you get graph view, backlinks, and search for free. Concept cards with `[[wikilinks]]` light up the graph automatically.

Everything is local. No cloud, no accounts, no sync. The vault is files on your disk. `cat` them, `grep` them, back them up with git.

## How Q&A works

The Chrome extension has a Notes tab where you can ask questions scoped to a thread, a concept, or the whole vault. Under the hood, it shells out to `claude -p` via a native messaging bridge — uses your existing Claude Code subscription, no separate API key.

Thread-scoped: "What are the open questions in this thread?" → 10 seconds, answer with citations to specific journal entries.

Concept-scoped: "Tell me about feedback and reward signals" → loads the concept card plus referencing threads, answers with cross-thread synthesis.

Corpus-wide: "What should I work on next?" → reads all structured notes, identifies convergence, suggests specific actions grounded in your own thinking.

The key insight: pre-computed synthesis (structured notes, concept cards) means the LLM doesn't have to discover connections at query time. They're already there. Queries are fast because the hard thinking was done during processing.

## What I got wrong, then right

**Concept pages were too long.** First version: 60-line essays with five sections, detailed per-thread summaries, and exhaustive open questions lists. Felt like AI-generated research papers. Nobody would re-read them.

The fix: concept cards should be 10 lines. Name the pattern, state the tension, pose one question, link to the evidence. Everything else is derivable on demand. Concept pages are indexes into understanding, not the understanding itself.

**Classification was too dumb.** First version: Python keyword matching against thread summaries. Kept filing things into the wrong thread because one thread had a keyword-rich summary that matched everything.

The fix: LLM classification. After you hit Capture, Claude reads your thread descriptions and the capture content, decides which thread(s) it belongs to. Takes ~5 seconds, but it's actually smart. A capture about "GRPO for corrective feedback in tutoring" correctly files to both the SLM research thread AND the education thread.

**The LLM voice was too AI.** First version: "Both domains are converging on the same architectural choice." Nobody talks like that in their own notes.

The fix: a persona. "You're a sharp friend who's been reading all their notes and just noticed something they missed. You think out loud. You use 'you' and 'your.' You don't say 'both domains converge' — you say 'this is the same problem showing up in two places.'"

## Design principles

1. **Capture should be ambient.** If it takes more than 5 seconds to log a thought, the habit dies. Every surface (CLI, browser, future: voice, mobile) exists to lower friction.

2. **Organization is the LLM's job.** The user never files, tags, or categorizes. Capture goes in, the system classifies, processes, and connects. The user's job is to think and capture. The system's job is to organize and surface.

3. **Concept cards are patterns, not essays.** 10 lines. Name it, link it, move on. Detail on demand.

4. **The vault compounds.** Each new capture enriches the network. Concept cards get stronger when threads reference them. New connections emerge that make old captures more valuable.

5. **Local-first, always.** Plain markdown. No cloud. No vendor lock-in. `git push` is your backup. The vault will outlive any product.

## The technical stack

- **Claude Code skill** (SKILL.md) — defines capture, query, process, and ask intents as natural-language instructions
- **Chrome Extension** (Manifest V3, side panel) — capture + Notes tab with Q&A
- **Native Messaging Bridge** (Python) — the extension talks to a local Python script that reads/writes the vault and shells out to `claude -p` for LLM operations
- **Obsidian** — free graph view, search, and editing on top of the markdown vault
- **No database, no server, no framework** — just files, a Python script, and Claude

Total codebase: ~2000 lines. The LLM does the heavy lifting.

## Where this is going

**Web dashboard.** A local `localhost:3137` page where you open your vault in a browser, ask questions, see concept graphs, review your week. The "Sarah's Sunday morning" experience — five minutes to see what you've been thinking about and plan what's next.

**Auto-processing.** Right now, processing is manual. The right model (borrowed from the Generative Agents paper) is tiered consolidation: immediate classification on capture, per-thread synthesis when things change, deep cross-thread concept extraction periodically. The brain doesn't rewrite all memories every night — it consolidates selectively.

**More capture surfaces.** Voice memos from your phone. Clipboard monitoring. RSS feeds. Slack DMs to yourself. Every surface that feeds raw thinking into the vault makes the concept layer richer.

**Concept strength and decay.** Concepts that keep getting referenced grow stronger. Concepts that stop being referenced fade. This mirrors the brain's forgetting curves — active pruning keeps the signal clean.

Karpathy wrote: "I think there is room here for an incredible new product instead of a hacky collection of scripts." I agree. The pattern — raw captures compiled by an LLM into a persistent, interconnected knowledge artifact — is too powerful to stay a side project.

The difference from a wiki: the vault isn't organized by topic. It's organized by connection. The concept graph IS the organization. You don't file things; you capture them, and the system tells you what connects.

---

Vibenote is open source: [github.com/gitcloned/vibenote](https://github.com/gitcloned/vibenote)

If this resonates — if you have threads of thinking that keep getting lost, connections that only surface weeks later, a sense that your notes should be working harder for you — try it. Or just read the code. The architecture is the interesting part.
