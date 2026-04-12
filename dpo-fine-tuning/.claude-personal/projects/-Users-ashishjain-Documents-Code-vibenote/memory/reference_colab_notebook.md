---
name: Fluento DPO Colab notebook
description: Link to the Colab notebook used for DPO fine-tuning Fluento tutor model, with training results and Gemini comparison
type: reference
---

Colab notebook for Fluento DPO fine-tuning: https://colab.research.google.com/drive/1lWTpRlt_NQ0NmEPwYxaeqDAtNgIUbnz_

**Status as of 2026-04-08:**
- Training completed (120 steps, 2 epochs on 500 DPO pairs)
- Base model: Qwen/Qwen2.5-7B-Instruct (4-bit quantized)
- LoRA adapter saved to Colab local filesystem (`/content/fluento-dpo-lora/`)
- Merged model saved to local filesystem (`/content/fluento-merged/`)
- NOT yet copied to Google Drive — needs to be done when Colab quota resets
- Comparison with Gemini Flash 2.5 was run, results in Google Sheet: https://docs.google.com/spreadsheets/d/1fCdLBPuDSjoKUTvgT3jTsoq1RZhUwN8QfjsN74HX81o/edit?gid=0#gid=0
- Eval pairs NOT yet pushed to Firestore

**Resume checklist (when Colab quota resets):**
1. Open notebook, connect to GPU runtime
2. Re-run Cell 1 (install) and Cell 3 (load base model)
3. Re-run Cell 4 (add LoRA) and Cell 7 (train) — OR if adapter was saved to Drive, use inference notebook instead
4. Copy to Drive: `!cp -r /content/fluento-dpo-lora /content/drive/MyDrive/fluento-dpo-lora`
5. Run Step 11 cells to push eval pairs to Firestore
