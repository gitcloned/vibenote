---
slug: test-slm-research
description: Research on training small language models using reinforcement learning
created: 2026-04-01T00:00:00Z
updated: 2026-04-06T00:00:00Z
entry_count: 3
---

# SLM Research

## Structured Note
**Thesis:** Small language models can achieve reasoning capabilities comparable to large models through reinforcement learning techniques, specifically GRPO and RLVR.

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
