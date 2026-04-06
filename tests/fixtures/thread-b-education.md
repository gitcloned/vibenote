---
slug: test-education-research
description: AI tutoring for children using adaptive reinforcement learning techniques
created: 2026-04-02T00:00:00Z
updated: 2026-04-05T00:00:00Z
entry_count: 2
---

# Education AI Research

## Structured Note
**What this is about:** Building an AI tutor that adapts to student performance using reinforcement learning feedback loops.

**Decisions made:**
- Focus on spoken English for children (K-12)
- Use task-based activities, not grammar drills
- Corrective feedback should adapt based on student proficiency level

**Current direction:** Exploring whether RL-based models can learn to scaffold feedback — starting with gentle recasts for beginners, escalating to explicit correction for advanced learners. This mirrors how human tutors intuitively adapt.

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
The connection between RL reward signals and corrective feedback is interesting. A recast is like a soft reward signal — it confirms the student was close.
