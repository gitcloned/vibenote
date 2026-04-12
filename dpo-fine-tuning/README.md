# Fluento DPO Preference Pairs

500 preference pairs for Direct Preference Optimization (DPO) fine-tuning of a voice-to-voice English language tutor.

## Format

`data/fluento_dpo_500.jsonl` — one JSON object per line:

```json
{
  "id": 1,
  "dimension": "scaffolding",
  "learner_level": "beginner",
  "prompt": "How do I say 'I am hungry' in English?",
  "chosen": "Let's figure it out together! ...",
  "rejected": "The answer is 'I am hungry'. Please repeat after me."
}
```

**Fields:**
- `prompt` — student utterance or question
- `chosen` — preferred tutor response (the behavior we want)
- `rejected` — rejected tutor response (the behavior we want to suppress)
- `dimension` — which behavioral quality the pair tests
- `learner_level` — beginner, intermediate, or advanced
- `id` — sequential identifier (1–500)

## Source & Methodology

**Source:** Fully synthetic — no real student data.

**Generation method:** Hybrid of hand-crafted seed pairs (~50) and programmatic template expansion. The generator script (`gen_dpo.py`) uses:
1. **50 hand-written seed pairs** across all 5 dimensions, reviewed for quality
2. **Template expansion** over word lists (irregular verbs, phrasal verbs, preposition errors, confusable words, etc.) to generate varied prompt-response combinations
3. **Deduplication** by 80-char prompt prefix to remove near-duplicates
4. **Shuffle** to mix dimensions and levels before final trim to 500

No external API calls — all responses are authored in the templates.

## Behavioral Dimensions

Each pair encodes a clear preference along one of five tutor behavior dimensions:

| Dimension | Count | What "chosen" does | What "rejected" does |
|-----------|-------|--------------------|--------------------|
| scaffolding | 113 | Asks leading questions, builds on what the learner knows | Gives the answer directly |
| difficulty_calibration | 100 | Matches response complexity to learner level | Over-shoots (jargon for beginners) or under-shoots (basics for advanced) |
| error_correction | 98 | Encouraging recast, explains the fix warmly | Blunt "Wrong. The correct answer is..." |
| verbosity | 98 | Concise, voice-friendly (1-2 sentences) | Long, text-style paragraphs |
| turn_taking | 91 | Clean handoff — responds briefly, invites learner to speak | Monologues — dumps information without pause |

## Learner Level Distribution

| Level | Count |
|-------|-------|
| beginner | 188 |
| intermediate | 194 |
| advanced | 118 |

## Quality Validation

- 0 exact prompt duplicates
- 0 empty fields
- 50-pair random sample reviewed: all pairs have clear, defensible preference direction
- All 500 records parse as valid JSON

## Usage

Generate the dataset:
```bash
python3 gen_dpo.py
```

For DPO training with TRL + Unsloth, map fields to the expected format:
```python
from datasets import load_dataset
dataset = load_dataset("json", data_files="data/fluento_dpo_500.jsonl")
```
