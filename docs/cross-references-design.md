# Cross-References & Entity Pages — Design, Implementation, and Testing

> **Issue:** [gitcloned/vibenote#1](https://github.com/gitcloned/vibenote/issues/1)
> **Branch:** `feat/cross-references`
> **Status:** Design complete. Implementation pending.

---

## 1. Why this feature exists

### The problem

Each Vibenote thread is an island. A concept like "GRPO" or "corrective feedback" may appear across multiple threads, but there is no mechanism to surface these connections. The user has to remember that both threads mention the concept and explicitly ask a cross-thread question. Most connections go unnoticed.

The vault grows linearly: adding a new thread adds no value to existing threads. There is no network effect.

### What changes for the user

Cross-references turn Vibenote from a filing cabinet into a thinking partner that notices connections the user missed.

| Without concepts | With concepts |
|---|---|
| Navigate by where you put things (threads) | Navigate by what you're thinking about (concepts) |
| Vault is a filing cabinet with labeled tabs | Vault is a web of interconnected ideas |
| Value grows linearly with captures | Value compounds — each capture enriches the network |
| User does the connecting in their head | System surfaces connections user missed |
| "What should I work on next?" draws from threads independently | The system sees convergence across threads and generates specific proposals |

### Concrete examples of new capability

1. **Cross-thread insight.** "Corrective feedback" (education thread) and "reward models" (SLM thread) are structurally the same problem — how to give a learner (human or model) useful feedback without overwhelming them. A concept page surfaces this parallel. The user never explicitly connected them.

2. **Convergence detection.** Three active concepts — GRPO, corrective feedback, model evaluation — are converging. The system generates: "Could you test a GRPO-distilled model specifically for corrective feedback in your tutoring use case? This would advance all three lines of research simultaneously."

3. **Gap identification.** A concept referenced in 4 threads but never deeply explored signals: "This keeps coming up. Maybe it deserves its own dedicated research thread."

### What doesn't change

- Capture flow stays the same
- Quick captures stay quick
- Processing is still manual (V1)
- Thread-scoped Q&A remains valuable
- Concepts are derived, not user-created

---

## 2. Design

### Architecture: three-tier memory (validated by four fields)

```
Journals (raw captures)
    ↓ process (per-thread)
Structured Notes (per-thread synthesis)
    ↓ process-all (cross-thread)
Concept Pages (cross-thread synthesis)
```

This three-tier model is independently validated by:
- **Cognitive science:** hippocampus (fast, raw) → neocortex (slow, stable, synthesized)
- **AI research:** Generative Agents (Stanford 2023) — observations → reflections → higher-order reflections
- **Knowledge management:** Zettelkasten — fleeting notes → literature notes → permanent notes
- **Software architecture:** Event sourcing — event log → materialized views → derived views

### Research foundations

| Source | Key insight applied |
|---|---|
| **Generative Agents (Stanford 2023)** | Three-tier memory architecture. Retrieval scoring: `recency × importance × relevance`. Periodic reflection generates higher-order understanding. |
| **MemoryBank (2023)** | Ebbinghaus forgetting curves for memory strength. Memories reinforced on access. Unused memories decay. |
| **Zettelkasten (Luhmann)** | Atomic notes, dense bidirectional links. Value comes from connections, not content. Associative topology over hierarchical taxonomy. |
| **Evergreen Notes (Matuschak)** | Notes should be concept-oriented, not source-oriented. Writing notes IS the thinking. |
| **Event Sourcing (CQRS)** | Immutable event log → derived materialized views. Any view can be rebuilt from the log. |
| **Entity Resolution (KG research)** | Detecting when two mentions refer to the same entity = concept merging. LLM-as-resolver is sufficient at small scale. |

### Processing approach: V1 vs. future

**V1: Full rewrite.**

Every `process all` regenerates all structured notes and all concept pages from journals. Simple, consistent, no drift.

- **Cost at current scale (3 threads):** ~30 seconds, 3-5 LLM calls
- **Cost at 20 threads:** ~3-5 minutes, 20-25 LLM calls
- **Cost at 50 threads:** ~10-15 minutes, 50-60 LLM calls (migration trigger)
- **Confidence: 7/10** — correct approach for V1, will need migration at ~20-30 threads

**Future (V2+): Tiered consolidation (brain-inspired).**

Three processing tiers at different frequencies:

| Tier | When | What | Cost |
|---|---|---|---|
| Immediate | Every capture | Classify, tag concepts, update counts | ~5s (existing LLM classifier) |
| Thread consolidation | On `process <slug>` | Regenerate one thread's structured note, flag concept changes | ~10s, 1 LLM call |
| Deep synthesis | On `process all` | Re-evaluate flagged concepts, generate/update concept pages, detect new connections | Proportional to flagged items only |

Migration from V1 to V2 requires adding `last_processed` timestamps and change flags. The journal remains the source of truth in both approaches — all derived state can be rebuilt.

### Concept lifecycle

**Emergence:**
- During `process all`, the LLM reads all structured notes
- A concept is "born" when it appears meaningfully in 2+ threads
- "Meaningfully" is an LLM judgment — not keyword matching, but semantic relevance
- Initial concept page: description, where it appears, brief synthesis

**Evolution:**
- Each `process all` re-evaluates existing concepts against current structured notes
- New perspectives integrated, connections updated, open questions refined
- Strength recalculated (see scoring below)

**Fading:**
- Strength drops below threshold → marked `state: fading` in frontmatter
- Shown dimmed in UI, deprioritized in queries
- Not deleted — knowledge shouldn't be destroyed, just deprioritized

**Merging:**
- LLM detects two concepts with high overlap during `process all`
- V1: auto-merge with a note in the concept page recording the merge
- V2: propose merge, user confirms
- One concept becomes primary, the other becomes an alias (redirect)

**Archival:**
- After 60+ days of fading with no new references → moved to `concepts/archived/`
- Still accessible, not shown in active views
- Can be revived if a new capture references the concept

### Concept strength scoring

Inspired by Generative Agents retrieval scoring and MemoryBank forgetting curves:

```
strength(concept) = Σ per referencing thread (
    substantiveness(thread, concept)
    × recency_decay(days_since_thread_updated)
)

recency_decay(days) = e^(-0.03 × days)
  → 1.0 at 0 days, 0.74 at 10 days, 0.55 at 20 days, 0.17 at 60 days

substantiveness: LLM-judged score 0.0-1.0
  → 1.0 if concept is a core topic of the thread
  → 0.3 if concept is mentioned but not central
```

Additionally, `last_accessed` is tracked. When a concept is queried, the access reinforces it:

```
effective_strength = strength + access_boost(days_since_last_accessed)
access_boost(days) = 0.5 × e^(-0.05 × days)
```

This implements the reconsolidation insight: **concepts you actively use persist longer than concepts you don't.**

### File structure

```
~/.vibenote/
├── threads/                     # existing
│   ├── slm-optimization-research.md
│   └── ai-education-research.md
├── concepts/                    # NEW
│   ├── index.md                 # concept catalog
│   ├── grpo.md                  # concept page
│   ├── corrective-feedback.md
│   └── archived/                # faded concepts
├── meta/
│   ├── index.md                 # thread index (existing)
│   ├── usage.log                # NEW — operation log
│   └── config.json              # existing
```

### Concept page template

```markdown
---
slug: grpo
type: concept
description: Group Relative Policy Optimization — RL algorithm for training LMs without a critic network
threads:
  - slm-optimization-research
  - ai-education-research
strength: 1.45
substantiveness:
  slm-optimization-research: 1.0
  ai-education-research: 0.3
first_seen: 2026-04-04
last_updated: 2026-04-06
last_accessed: null
state: active
---

# GRPO (Group Relative Policy Optimization)

## What I know
<Synthesized understanding from ALL referencing threads. Not a copy — a genuine
multi-perspective synthesis that generates connections the individual threads don't make.>

## Where it appears
- **slm-optimization-research:** <how this thread discusses the concept>
- **ai-education-research:** <how this thread discusses the concept>

## Open questions
- <Questions about this concept that span threads or aren't answered in any thread>

## Connections
- Related to: [[rlvr]], [[corrective-feedback]]
- Tension with: [[mcts]]
```

### Wikilinks in structured notes

After generating concept pages, the processor inserts `[[concept-slug]]` wikilinks into structured notes where concepts are mentioned. This lights up Obsidian's graph view automatically.

Example: in `slm-optimization-research`'s structured note, "GRPO" becomes "[[grpo|GRPO]]".

### Usage per surface

| Surface | Concept interaction | Primary job |
|---|---|---|
| **Claude Code CLI** | `process all` generates concepts. `what concepts emerged?` lists them. `tell me about [[feedback]]` reads a concept page. `merge X and Y` triggers merge. | Gardening — create, maintain, prune |
| **Chrome extension** | Notes tab gains concept picker alongside thread picker. Quick queries scope to concepts. Capture shows concept tags in status. | Quick lookup — reference during reading |
| **Web dashboard** (future) | Concept graph visualization. "Most active concepts this week." Concept health indicators. | Reflection — see the whole network |

---

## 3. Implementation plan

### Task list

Each task is independently shippable and testable.

#### Phase 1 — Foundation

- [ ] **T1: Add usage logging to bridge** — append one line per operation to `~/.vibenote/meta/usage.log`. Format: `<timestamp> op=<op> scope=<scope> latency_ms=<ms>`. ~10 lines in bridge.
- [ ] **T2: Create `~/.vibenote/concepts/` directory** — add to `setup.sh`. Create `concepts/index.md` template.
- [ ] **T3: Write test fixtures** — synthetic test threads in `tests/fixtures/` for automated testing. Two shared-concept threads, two unrelated threads.
- [ ] **T4: Write structural test scaffold** — `tests/test_concepts.py` with tests 1-4 (emergence, no false concepts, wikilinks, strength). Tests fail initially (TDD).

#### Phase 2 — Concept extraction and page generation

- [ ] **T5: Concept extraction prompt** — given all structured notes, extract concepts that appear in 2+ threads. Return JSON: `[{slug, description, threads, substantiveness_per_thread}]`.
- [ ] **T6: Concept page generation** — for each extracted concept, generate a full concept page using the template. Write to `~/.vibenote/concepts/<slug>.md`.
- [ ] **T7: Concept index generation** — `~/.vibenote/concepts/index.md` listing all active concepts with strength, thread count, state.
- [ ] **T8: Strength scoring** — implement the scoring function with recency decay. Store in concept frontmatter.
- [ ] **T9: Wikilink insertion** — after generating concept pages, insert `[[concept]]` wikilinks into structured notes where concepts are mentioned.

#### Phase 3 — Integration with existing features

- [ ] **T10: Update `process all` flow** — extend the Vibenote SKILL.md "On process" instructions to include concept extraction after thread processing.
- [ ] **T11: Bridge `read-concept` op** — new operation for the extension to read a concept page.
- [ ] **T12: Bridge `list-concepts` op** — return concept index for the extension dropdown.
- [ ] **T13: Notes tab concept picker** — add concept section to the thread/scope selector in the extension. Scope ask queries to a concept.
- [ ] **T14: Capture concept tagging** — after LLM classification, include concept tags in the capture response. Show in extension status.

#### Phase 4 — Testing and validation

- [ ] **T15: Run structural tests** — all tests from T4 pass.
- [ ] **T16: LLM-as-judge quality tests** — evaluate concept page quality on the real vault (synthesis, accuracy, insight, actionability scores).
- [ ] **T17: Before/after ask comparison** — run baseline queries with concepts, compare to saved baselines.
- [ ] **T18: Create `vibenote-observations` thread** — meta-thread for user reactions during the 2-week evaluation.
- [ ] **T19: Usage log analysis script** — `scripts/vn-usage-analysis.sh` that computes concept adoption ratio, engagement over time, never-queried concepts.

#### Phase 5 — Polish and concept lifecycle

- [ ] **T20: Concept fading** — during `process all`, mark concepts below strength threshold as `state: fading`.
- [ ] **T21: Concept merging** — during `process all`, detect overlapping concepts and auto-merge.
- [ ] **T22: `last_accessed` tracking** — bump when a concept is queried. Factor into effective strength.
- [ ] **T23: Concept-aware ask prompts** — when asking about a thread, include relevant concept pages as additional context for richer answers.

### Build order

T1 → T2 → T3 → T4 (foundation + tests first)
→ T5 → T6 → T7 → T8 → T9 (core concept generation, run tests at each step)
→ T10 → T15 (integrate with process flow, verify all structural tests pass)
→ T11 → T12 → T13 → T14 (extension integration)
→ T16 → T17 → T18 (quality validation)
→ T19 → T20 → T21 → T22 → T23 (polish, lifecycle, advanced features)

---

## 4. Testing plan

### Test types

| # | Test name | Type | Automated? | When to run |
|---|---|---|---|---|
| 1 | Concept emergence | Structural | ✅ Yes | Every build |
| 2 | No false concepts | Structural | ✅ Yes | Every build |
| 3 | Wikilink correctness | Structural | ✅ Yes | Every build |
| 4 | Strength scoring | Structural | ✅ Yes | Every build |
| 5 | Concept quality (LLM-as-judge) | Quality | ✅ Yes (~10s/concept) | After prompt changes |
| 6 | Ask quality improvement | Quality | ✅ Yes | After first process-all |
| 7 | Usage pattern analysis | Value | Semi-automated | At 2-week mark |

### Test 1: Concept emergence from known content

**Setup:** Two synthetic threads that both discuss "reinforcement learning."

```
tests/fixtures/thread-a-slm.md:
  Structured Note about GRPO, RLVR, reinforcement learning for SLMs.

tests/fixtures/thread-b-education.md:
  Structured Note about RL-based adaptive tutoring, feedback loops.
```

**Expected:**
- A concept `reinforcement-learning` (or similar) emerges
- Its `threads` field includes both thread slugs
- Its "What I know" section mentions both SLM training and tutoring contexts

**Assertion:**
```python
assert concept_exists("reinforcement-learning") or concept_exists_matching("reinforcement")
assert len(concept.threads) >= 2
assert len(concept.what_i_know) > 100  # not just a stub
```

### Test 2: No false concepts from unrelated threads

**Setup:** Two synthetic threads with zero topical overlap.

```
tests/fixtures/thread-cooking.md:
  Structured Note about Italian pasta recipes.

tests/fixtures/thread-javascript.md:
  Structured Note about JS event loop and async patterns.
```

**Expected:** No concept pages generated.

**Assertion:**
```python
assert len(list_concepts()) == 0
```

### Test 3: Wikilink correctness

**Setup:** Real vault after `process all`.

**Assertions:**
```python
for concept in list_concepts():
    # Every concept has ≥ 2 referencing threads
    assert len(concept.threads) >= 2

    # Every referencing thread has the wikilink
    for slug in concept.threads:
        note = read_structured_note(slug)
        assert f"[[{concept.slug}" in note  # allows [[slug|Display Text]]

# No dangling wikilinks
for thread in list_threads():
    note = read_structured_note(thread.slug)
    for link in extract_wikilinks(note):
        assert concept_exists(link), f"Dangling: [[{link}]] in {thread.slug}"
```

### Test 4: Strength scoring

**Setup:** Three synthetic threads referencing the same concept with different recency.

```
thread-recent:  updated today, core reference (substantiveness=1.0)
thread-older:   updated 20 days ago, core reference (substantiveness=1.0)
thread-stale:   updated 60 days ago, passing mention (substantiveness=0.3)
```

**Expected:**
```python
# Strength formula: Σ substantiveness × e^(-0.03 × days)
# recent: 1.0 × e^0 = 1.0
# older:  1.0 × e^(-0.6) ≈ 0.55
# stale:  0.3 × e^(-1.8) ≈ 0.05
# Total ≈ 1.60

concept = read_concept("test-concept")
assert 1.2 < concept.strength < 2.0  # fuzzy bounds for LLM variance
assert concept.strength > 1.0  # recent thread alone contributes 1.0
```

### Test 5: Concept quality — LLM-as-judge

**Evaluation prompt sent to Claude:**

```
Evaluate this concept page from a personal knowledge base.

CONCEPT PAGE:
{page_content}

SOURCE THREADS:
{referencing_structured_notes}

Score 1-5 on each dimension:
1. SYNTHESIS: Synthesizes across threads (5) vs. just lists appearances (1)
2. ACCURACY: Faithfully represents source threads (5) vs. distorts/hallucinates (1)
3. INSIGHT: Surfaces non-obvious connections (5) vs. restates the obvious (1)
4. ACTIONABILITY: Suggests next steps or open questions (5) vs. purely descriptive (1)

Return ONLY JSON: {"synthesis": N, "accuracy": N, "insight": N, "actionability": N}
```

**Pass criteria:**
- `synthesis >= 3` (more than listing)
- `accuracy >= 4` (no hallucination)
- `insight >= 2` (at least one non-obvious connection)
- Average across all concepts >= 3.0

**Calibration:** Before trusting the judge, run it on one hand-crafted "good" concept page and one hand-crafted "bad" one. Verify the scores align with human judgment.

### Test 6: Ask quality improvement (before/after)

**Baseline queries** (saved before concepts exist):

```json
{
  "queries": [
    "What connects my research threads?",
    "What should I work on next?",
    "What common themes run across my work?"
  ]
}
```

**Procedure:**
1. Run each query WITHOUT concepts → save answers
2. Run `process all` → generate concepts
3. Run each query WITH concepts → save answers
4. For each query, LLM-as-judge: "Which answer is more insightful, specific, and actionable? A or B?"

**Pass criteria:** "After" wins ≥ 2 out of 3 comparisons.

### Test 7: Usage pattern analysis (2-week mark)

**Data source:** `~/.vibenote/meta/usage.log`

**Metrics computed:**

```
1. Concept adoption ratio = concept_asks / (concept_asks + thread_asks)
   Signal: >20% = concepts are a natural navigation unit

2. Engagement trend = week2_concept_asks / week1_concept_asks
   Signal: >1.0 = adoption growing; <0.5 = novelty wore off

3. Coverage utilization = concepts_ever_queried / total_concepts
   Signal: <20% = generating too many concepts; >50% = right number

4. Observation thread sentiment = process vibenote-observations thread,
   count positive vs negative reactions
   Signal: more positive = feature is valued
```

**Decision matrix at 2-week mark:**

| Metric | Invest more | Tune prompts | Deprioritize |
|---|---|---|---|
| Concept adoption ratio | >20% | 5-20% | <5% |
| Engagement trend | >1.0 | 0.5-1.0 | <0.5 |
| Coverage utilization | 30-70% | >70% (too few) or <30% (too many) | <10% |
| Observation sentiment | Mostly positive | Mixed | Mostly negative |
| "Would you miss concepts?" | Yes | Unsure | No |

---

## 5. Test data fixtures

### Fixture 1: Shared-concept threads (for test 1)

**File:** `tests/fixtures/thread-a-slm.md`
```markdown
---
slug: test-slm-research
description: Research on training small language models using reinforcement learning
created: 2026-04-01T00:00:00Z
updated: 2026-04-06T00:00:00Z
entry_count: 3
---

# SLM Research

## Structured Note
**Thesis:** Small language models can achieve reasoning capabilities comparable to
large models through reinforcement learning techniques, specifically GRPO and RLVR.

**Key concepts:**
- GRPO eliminates the need for a critic network, reducing VRAM requirements
- Reinforcement learning with verifiable rewards produces more robust training than MCTS
- Models trained with RL spontaneously develop self-correction behavior

**Open questions:**
- Can RL-trained small models generalize beyond math/code to open-ended domains?
- What's the minimum dataset size for effective GRPO training?

---

## My Notes
*Your space.*

---

## Journal

### 2026-04-01T00:00:00Z
Initial research dump about GRPO and SLM training approaches.

### 2026-04-03T00:00:00Z
Read about RLVR — uses compilers and string matching instead of AI judges.

### 2026-04-06T00:00:00Z
Thinking about whether RL training could work for non-math tasks like tutoring.
```

**File:** `tests/fixtures/thread-b-education.md`
```markdown
---
slug: test-education-research
description: AI tutoring for children using adaptive reinforcement learning techniques
created: 2026-04-02T00:00:00Z
updated: 2026-04-05T00:00:00Z
entry_count: 2
---

# Education AI Research

## Structured Note
**What this is about:** Building an AI tutor that adapts to student performance
using reinforcement learning feedback loops.

**Decisions made:**
- Focus on spoken English for children (K-12)
- Use task-based activities, not grammar drills
- Corrective feedback should adapt based on student proficiency level

**Current direction:** Exploring whether RL-based models can learn to scaffold
feedback — starting with gentle recasts for beginners, escalating to explicit
correction for advanced learners. This mirrors how human tutors intuitively adapt.

**Open questions:**
- Which RL training approach produces the best scaffolding behavior in tutoring models?
- Can we use GRPO-style training to fine-tune a small model specifically for tutoring?

---

## My Notes
*Your space.*

---

## Journal

### 2026-04-02T00:00:00Z
Want to explore AI tutoring. Thinking about how RL could make feedback adaptive.

### 2026-04-05T00:00:00Z
The connection between RL reward signals and corrective feedback is interesting.
A recast is like a soft reward signal — it confirms the student was close.
```

**Expected concepts from these two threads:**
- `reinforcement-learning` — both threads discuss RL as a training/adaptation mechanism
- `grpo` — mentioned in both (SLM training + potential tutoring model training)
- Potentially `feedback` or `corrective-feedback` — SLM thread's reward signals ↔ education thread's corrective feedback

### Fixture 2: Unrelated threads (for test 2)

**File:** `tests/fixtures/thread-cooking.md`
```markdown
---
slug: test-cooking
description: Italian pasta recipes and techniques
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:00:00Z
entry_count: 1
---

# Italian Cooking

## Structured Note
**What this is about:** Collecting authentic Italian pasta recipes.

**Recipes explored:**
- Cacio e pepe — requires proper starch water technique
- Carbonara — eggs must be tempered, not scrambled
- Aglio e olio — simplicity demands perfect execution

---

## My Notes
*Your space.*

---

## Journal

### 2026-04-01T00:00:00Z
Started collecting pasta recipes. The key insight: Italian cooking is about
technique with simple ingredients, not complex preparations.
```

**File:** `tests/fixtures/thread-javascript.md`
```markdown
---
slug: test-javascript
description: JavaScript event loop and async programming patterns
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:00:00Z
entry_count: 1
---

# JavaScript Performance

## Structured Note
**What this is about:** Understanding the JS event loop for performance optimization.

**Key concepts:**
- Microtasks (Promises) run before macrotasks (setTimeout)
- Async/await is syntactic sugar over Promise chains
- Event loop starvation happens when microtasks never yield

---

## My Notes
*Your space.*

---

## Journal

### 2026-04-01T00:00:00Z
Deep dive into how the event loop actually works under the hood.
```

**Expected:** Zero concepts emerge from these two threads.

### Fixture 3: Baseline query answers

**File:** `tests/fixtures/baseline-answers.json`

*(To be populated by running the three baseline queries against the current vault BEFORE concepts exist. See Task T35.)*

```json
{
  "generated_at": "<timestamp>",
  "vault_state": {
    "threads": ["slm-optimization-research", "ai-education-research", "reading-list"],
    "concepts_exist": false
  },
  "queries": [
    {
      "question": "What connects my research threads?",
      "answer": "<to be filled>"
    },
    {
      "question": "What should I work on next?",
      "answer": "<to be filled>"
    },
    {
      "question": "What common themes run across my work?",
      "answer": "<to be filled>"
    }
  ]
}
```

---

## 6. Validation timeline

| When | Action | Success signal |
|---|---|---|
| **Day 0** | Ship V1. Generate initial concepts from 3 threads. Open in Obsidian. | Are any concepts surprising? |
| **Day 0** | Run before/after ask comparison (test 6). | "After" wins ≥ 2/3 comparisons |
| **Day 1-7** | Use normally. Capture via extension, query via Notes tab. | Do you naturally gravitate to concepts? |
| **Day 7** | Mid-point check: review usage.log, read vibenote-observations thread. | Concept queries > 0? Positive reactions? |
| **Day 14** | Full evaluation: run test 7 metrics, answer the three questions. | 2/3 positive → invest. 0/3 → reconsider. |

### The three questions (end of week 2)

1. **Did any concept page tell you something you didn't already know?**
   - Yes → extraction is working
   - No → prompts need tuning, or vault too small

2. **Did you act on a concept-generated insight?**
   - Yes → concepts drive action
   - No → concepts are interesting but not actionable

3. **Would you miss concepts if they disappeared?**
   - Yes → core feature, invest in V2
   - No → deprioritize

---

## 7. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Concepts are too generic ("X appears in A and B") | Medium | High — feature feels useless | Tune the synthesis prompt to demand novel connections, not listings. Test 5 catches this. |
| Too many concepts generated (noise) | Medium | Medium — user drowns in low-value pages | Set minimum substantiveness threshold. Strength scoring naturally deprioritizes weak concepts. |
| Processing time too slow at scale | Low (V1 scale) | Medium — user stops processing | Monitor processing time. Migrate to tiered approach (V2) when >2 minutes. |
| LLM hallucination in concept pages | Low | High — erodes trust | Accuracy score in test 5. Concept pages cite source threads; user can verify. |
| Wikilinks clutter structured notes | Low | Low — visual noise | Use `[[slug\|Display Text]]` format. Keep links inline, not as a separate section. |
| Full rewrite costs real money at scale | Low (V1) | Medium | Monitor API costs. ~$0.02 per concept page. At 30 concepts, ~$0.60 per process-all. Acceptable. |
