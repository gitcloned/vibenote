---
name: Fluento DPO fine-tuning project status
description: Current state of the DPO fine-tuning pipeline for Fluento English tutor — training done, eval site built, pending Drive save and Firestore seeding
type: project
---

**What this is about:** DPO fine-tuning a 7B SLM (Qwen 2.5 7B) to behave as a good English language tutor for Fluento, a voice-to-voice tutoring app with 400-800ms latency budget.

**Completed:**
- 500 DPO preference pairs generated (`data/fluento_dpo_500.jsonl`) covering 5 behavioral dimensions: scaffolding, verbosity, error correction, turn-taking, difficulty calibration
- Training completed on Colab free tier (T4 GPU, ~120 steps, trl==0.24.0, no Unsloth due to mergekit conflict)
- Side-by-side comparison with Gemini Flash 2.5 run, results in Google Sheet
- Blind A/B eval site built (`eval-site/index.html`) with Firebase Auth + Firestore
- Firebase project: `fluento-eval` (config already in index.html)
- Inference notebook documented (`INFERENCE_NOTEBOOK.md`) for loading saved adapter without retraining

**Pending (when Colab quota resets):**
- Copy LoRA adapter + merged model to Google Drive (critical — local Colab files are ephemeral)
- Push eval pairs to Firestore (Step 11 in COLAB_GUIDE)
- Deploy eval site to Firebase Hosting
- If adapter was lost due to disconnect, will need to retrain (~30 min)

**Why:** Standard DPO (not MCTS, not SDPO) was chosen because it has zero inference overhead — preferences are baked into model weights. 500 pairs is the minimum viable dataset for a first pass.

**How to apply:** When resuming, check if the adapter exists on Google Drive first. If not, retrain using the training notebook. Then use the inference notebook for all further testing.
