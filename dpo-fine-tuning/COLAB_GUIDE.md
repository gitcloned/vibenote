# DPO Fine-Tuning on Google Colab — Step-by-Step Guide

## Prerequisites
- Google account with access to [Google Colab](https://colab.research.google.com)
- Free tier works (T4 GPU) — Colab Pro (A100) is faster but not required
- The `fluento_dpo_500.jsonl` file from this repo
- ~30-45 minutes total (setup + training + testing)

---

## Step 1: Create a New Colab Notebook

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. Click **New Notebook**
3. Go to **Runtime → Change runtime type → T4 GPU** (or A100 if you have Pro)
4. Verify GPU is connected: run `!nvidia-smi` in a cell

---

## Step 2: Install Dependencies

> **Known issue (mid-2025):** Unsloth's latest release installs a TRL build that
> hard-depends on `mergekit`, which has a pydantic/torch conflict. The recommended
> path below skips Unsloth and installs clean dependencies directly. Training takes
> ~30 min on T4 instead of ~15 min — a worthwhile trade for zero install headaches.

```python
# Cell 1: Install dependencies (tested and verified — no Unsloth needed)
!pip install "trl==0.24.0" "transformers>=4.45" "peft>=0.13" "accelerate" "datasets" "bitsandbytes"
```

```python
# Cell 2: Verify — this MUST print "OK" before proceeding
from trl import DPOConfig, DPOTrainer
print("OK — DPO imports work!")
```

> **Optional: Unsloth path (if they fix mergekit in a future release)**
> ```python
> !pip install unsloth
> !pip uninstall unsloth -y && pip install --upgrade --no-cache-dir --no-deps unsloth
> ```
> Then use Cell 3A (Unsloth model loading) instead of Cell 3B below.

---

## Step 3: Upload Your Dataset

Option A — Upload manually:
- Click the folder icon in Colab's left sidebar
- Drag `fluento_dpo_500.jsonl` into the file browser

Option B — From Google Drive:
```python
# Cell 2 (optional): Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')
# Then copy your file:
# !cp /content/drive/MyDrive/path/to/fluento_dpo_500.jsonl /content/
```

---

## Step 4: Load the Base Model

```python
# Cell 3: Load model with 4-bit quantization
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# Pick ONE (uncomment your choice):

# RECOMMENDED — Best quality, fits T4 with 4-bit
model_name = "Qwen/Qwen2.5-7B-Instruct"

# ALTERNATIVE — Fastest training, smallest model
# model_name = "meta-llama/Llama-3.2-3B-Instruct"

# ALTERNATIVE — Latest Google model (March 2025)
# model_name = "google/gemma-3-4b-it"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.float16,
)

print(f"Model loaded: {model_name}")
```

---

## Step 5: Add LoRA Adapters

```python
# Cell 4: Configure LoRA for DPO
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=16,                    # LoRA rank — 16 is a good default
    lora_alpha=16,
    target_modules=[         # Which layers to adapt
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)

model.print_trainable_parameters()
print("LoRA adapters added!")
```

---

## Step 6: Prepare the Dataset

```python
# Cell 5: Load and format the DPO dataset
from datasets import load_dataset

dataset = load_dataset("json", data_files="/content/fluento_dpo_500.jsonl", split="train")

print(f"Loaded {len(dataset)} pairs")
print(f"Sample: {dataset[0]}")

# Format into chat template for DPO
# DPO expects: prompt (list of messages), chosen (response), rejected (response)

def format_for_dpo(example):
    """Convert our format to TRL DPO trainer format."""
    return {
        "prompt": [
            {"role": "system", "content": "You are Fluento, a friendly English language tutor for voice conversations. Keep responses short (1-2 sentences), ask guiding questions, and match the learner's level."},
            {"role": "user", "content": example["prompt"]},
        ],
        "chosen": [
            {"role": "assistant", "content": example["chosen"]},
        ],
        "rejected": [
            {"role": "assistant", "content": example["rejected"]},
        ],
    }

dpo_dataset = dataset.map(format_for_dpo)
print(f"Formatted {len(dpo_dataset)} pairs for DPO")
print(f"Keys: {list(dpo_dataset[0].keys())}")
```

---

## Step 7: Configure and Run DPO Training

```python
# Cell 6: Set up DPO trainer
from trl import DPOConfig, DPOTrainer

training_args = DPOConfig(
    output_dir="./fluento-dpo-output",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,    # Effective batch size = 8
    num_train_epochs=2,               # 2 epochs is usually enough for 500 pairs
    learning_rate=5e-6,               # Conservative LR for DPO
    beta=0.1,                         # DPO beta — controls how much to diverge from base
    max_length=1024,
    max_prompt_length=512,
    logging_steps=10,
    save_steps=100,
    warmup_ratio=0.1,
    optim="adamw_8bit",               # Memory-efficient optimizer
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    seed=42,
)

trainer = DPOTrainer(
    model=model,
    args=training_args,
    train_dataset=dpo_dataset,
    processing_class=tokenizer,
)

print("Trainer ready. Starting DPO fine-tuning...")
```

```python
# Cell 7: Train! (~15-30 min on T4, ~5-10 min on A100)
trainer.train()
print("Training complete!")
```

---

## Step 8: Test the Fine-Tuned Model

```python
# Cell 8: Quick test — compare base vs fine-tuned responses
model.eval()

test_prompts = [
    "What is the past tense of 'go'?",
    "I goed to the store yesterday.",
    "I want to learn English. I am new student.",
    "Can you explain what a phrasal verb is?",
    "I've been learning English for 10 years. Give me something challenging.",
]

for prompt in test_prompts:
    messages = [
        {"role": "system", "content": "You are Fluento, a friendly English language tutor for voice conversations. Keep responses short (1-2 sentences), ask guiding questions, and match the learner's level."},
        {"role": "user", "content": prompt},
    ]
    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True
    ).to("cuda")

    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
    )

    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    print(f"\n{'='*60}")
    print(f"STUDENT: {prompt}")
    print(f"FLUENTO: {response}")
```

---

## Step 9: Save the Model

```python
# Cell 9a: Save LoRA adapter locally (small, ~50MB)
model.save_pretrained("fluento-dpo-lora")
tokenizer.save_pretrained("fluento-dpo-lora")
print("LoRA adapter saved locally!")
```

```python
# Cell 9b: Save to Google Drive (persists across sessions)
from google.colab import drive
drive.mount('/content/drive')

import shutil
save_path = "/content/drive/MyDrive/fluento-dpo-lora"
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)
print(f"Model saved to Google Drive: {save_path}")
```

```python
# Cell 9c: (Optional) Push to HuggingFace Hub
# model.push_to_hub("your-username/fluento-dpo-lora")
# tokenizer.push_to_hub("your-username/fluento-dpo-lora")
```

```python
# Cell 9d: (Optional) Export merged model for local inference
# Merges LoRA weights into the base model — larger but standalone
merged_model = model.merge_and_unload()
merged_model.save_pretrained("fluento-merged")
tokenizer.save_pretrained("fluento-merged")
# Also save to Drive:
merged_model.save_pretrained("/content/drive/MyDrive/fluento-merged")
tokenizer.save_pretrained("/content/drive/MyDrive/fluento-merged")
print("Merged model saved! Convert to GGUF with llama.cpp for Ollama use.")
```

---

## Step 10: Compare with Gemini Flash 2.5

Side-by-side comparison of the DPO fine-tuned model vs Gemini Flash 2.5 using
the same system prompt and test scenarios.

```python
# Cell 10a: Install Gemini SDK
!pip install google-generativeai
```

```python
# Cell 10b: Configure Gemini
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY_HERE")  # <-- paste your Gemini API key
gemini = genai.GenerativeModel("gemini-2.5-flash")

SYSTEM = "You are Fluento, a friendly English language tutor for voice conversations. Keep responses short (1-2 sentences), ask guiding questions, and match the learner's level."

print("Gemini configured!")
```

```python
# Cell 10c: Run side-by-side comparison
test_prompts = [
    ("beginner",     "What is the past tense of 'go'?"),
    ("beginner",     "I goed to the store yesterday."),
    ("beginner",     "I want to learn English. I am new student."),
    ("intermediate", "Can you explain what a phrasal verb is?"),
    ("intermediate", "She said me that she was coming."),
    ("advanced",     "I've been learning English for 10 years. Give me something challenging."),
    ("advanced",     "Between you and I, she's going to resign."),
]

results = []

for level, prompt in test_prompts:
    # --- Fluento (DPO fine-tuned) ---
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]
    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True
    ).to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=150, temperature=0.7, top_p=0.9, do_sample=True)
    fluento_resp = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip()

    # --- Gemini Flash 2.5 ---
    gemini_resp = gemini.generate_content(
        f"{SYSTEM}\n\nStudent ({level} level): {prompt}"
    ).text.strip()

    results.append((level, prompt, fluento_resp, gemini_resp))

    # Print as we go
    print(f"\n{'='*70}")
    print(f"[{level.upper()}] STUDENT: {prompt}")
    print(f"\n  FLUENTO (DPO Qwen 7B):")
    print(f"  {fluento_resp}")
    print(f"\n  GEMINI FLASH 2.5:")
    print(f"  {gemini_resp}")
    print(f"\n  Length — Fluento: {len(fluento_resp)} chars | Gemini: {len(gemini_resp)} chars")
```

```python
# Cell 10d: Summary scorecard
print(f"\n{'='*70}")
print("SUMMARY SCORECARD")
print(f"{'='*70}")
print(f"\n{'Metric':<25} {'Fluento (DPO)':<20} {'Gemini Flash 2.5':<20}")
print(f"{'-'*65}")

fluento_lengths = [len(r[2]) for r in results]
gemini_lengths = [len(r[3]) for r in results]

print(f"{'Avg response length':<25} {sum(fluento_lengths)//len(fluento_lengths):<20} {sum(gemini_lengths)//len(gemini_lengths):<20}")
print(f"{'Max response length':<25} {max(fluento_lengths):<20} {max(gemini_lengths):<20}")
print(f"{'Min response length':<25} {min(fluento_lengths):<20} {min(gemini_lengths):<20}")

# Count responses that end with a question (scaffolding signal)
fluento_questions = sum(1 for r in results if '?' in r[2])
gemini_questions = sum(1 for r in results if '?' in r[3])
print(f"{'Asks a question':<25} {fluento_questions}/{len(results):<17} {gemini_questions}/{len(results):<17}")

# Count short responses (under 200 chars — good for voice)
fluento_short = sum(1 for r in results if len(r[2]) < 200)
gemini_short = sum(1 for r in results if len(r[3]) < 200)
print(f"{'Voice-friendly (<200ch)':<25} {fluento_short}/{len(results):<17} {gemini_short}/{len(results):<17}")

print(f"\nKey things to look for:")
print(f"  - Does Fluento ask leading questions instead of giving answers? (scaffolding)")
print(f"  - Are Fluento responses shorter? (verbosity control for voice)")
print(f"  - Does Fluento encourage the student to try again? (error correction style)")
print(f"  - Does Fluento match the complexity to the level tag? (difficulty calibration)")
```

---

## Step 11: Push Eval Pairs to Firestore (for blind evaluation site)

Push the comparison results directly to Firestore from this notebook.
Uses `prompt + model_a_name` as a composite key to prevent duplicates —
re-running this cell with the same data is safe.

```python
# Cell 11a: Install Firebase Admin SDK
!pip install firebase-admin
```

```python
# Cell 11b: Upload your Firebase service account key
# Download from: Firebase Console → Project Settings → Service Accounts → Generate New Private Key
from google.colab import files
uploaded = files.upload()  # Upload the JSON key file
SERVICE_ACCOUNT_KEY = list(uploaded.keys())[0]
print(f"Using key: {SERVICE_ACCOUNT_KEY}")
```

```python
# Cell 11c: Initialize Firebase
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib

# Only initialize once
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred)

db = firestore.client()
print("Firebase connected!")
```

```python
# Cell 11d: Push eval pairs with dedup
# Uses results from Cell 10c (the side-by-side comparison).
# If you want to add more prompts later, just extend test_prompts in 10c, re-run 10c, then re-run this cell.

MODEL_A_NAME = "fluento-dpo-v1"   # Change version when you retrain (v2, v3, etc.)
MODEL_B_NAME = "gemini-flash-2.5"

def make_pair_id(prompt, model_a_name):
    """Deterministic doc ID from prompt + model_a_name. Prevents duplicates."""
    raw = f"{prompt.strip().lower()}|{model_a_name.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]

pushed = 0
skipped = 0

for level, prompt, fluento_resp, gemini_resp in results:
    pair_id = make_pair_id(prompt, MODEL_A_NAME)
    doc_ref = db.collection("eval_pairs").document(pair_id)

    # Check if already exists
    if doc_ref.get().exists:
        skipped += 1
        continue

    doc_ref.set({
        "prompt": prompt,
        "level": level,
        "model_a_name": MODEL_A_NAME,
        "model_a_response": fluento_resp,
        "model_b_name": MODEL_B_NAME,
        "model_b_response": gemini_resp,
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    pushed += 1

print(f"Done! Pushed {pushed} new pairs, skipped {skipped} duplicates.")
print(f"Total pairs in Firestore: {pushed + skipped}")
```

```python
# Cell 11e: (Optional) Verify — list all pairs in Firestore
docs = db.collection("eval_pairs").stream()
for doc in docs:
    d = doc.to_dict()
    print(f"  [{d.get('level','')}] {d['prompt'][:60]}... → {d['model_a_name']} vs {d['model_b_name']}")
```

> **Adding a new model version later:**
> 1. Fine-tune v2, re-run inference (Cell 8)
> 2. Change `MODEL_A_NAME = "fluento-dpo-v2"` in Cell 11d
> 3. Re-run Cell 10c (comparison) and Cell 11d (push)
> 4. New pairs get new IDs (different model name = different hash), so old data is preserved
> 5. The eval site leaderboard automatically picks up the new model

---

## Step 12: Download and Test Locally (Optional)

```python
# Cell 12: Download the LoRA adapter
!zip -r fluento-dpo-lora.zip fluento-dpo-lora/
from google.colab import files
files.download("fluento-dpo-lora.zip")
```

Then on your Mac:
```bash
# Install Ollama (if not already)
brew install ollama

# Create a Modelfile (using the merged GGUF if you converted it)
cat > Modelfile << 'EOF'
FROM ./fluento-merged.gguf
SYSTEM "You are Fluento, a friendly English language tutor for voice conversations. Keep responses short (1-2 sentences), ask guiding questions, and match the learner's level."
PARAMETER temperature 0.7
EOF

# Create and run
ollama create fluento -f Modelfile
ollama run fluento "I goed to the store yesterday"
```

---

## What to Look For (Success Criteria)

After training, the fine-tuned model should:

| Behavior | Before DPO (base model) | After DPO (fine-tuned) |
|----------|------------------------|----------------------|
| Error correction | "The correct form is 'went'." | "Good try! 'Go' is irregular — try 'went'. Can you say the full sentence?" |
| Verbosity | Long paragraph explanations | 1-2 sentence responses |
| Scaffolding | Gives answers directly | Asks leading questions |
| Turn-taking | Monologues | Short response + invitation to speak |
| Difficulty | Same complexity for all levels | Adapts to learner level |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `CUDA out of memory` | Reduce `per_device_train_batch_size` to 1, or use a smaller model (3B) |
| `Runtime disconnected` | Colab free tier has time limits — use Colab Pro or save checkpoints frequently |
| Model outputs unchanged | Increase `num_train_epochs` to 3, or increase `learning_rate` to 1e-5 |
| Training loss not decreasing | Check dataset format — run `print(dpo_dataset[0])` to verify structure |
| `unsloth` install fails | Run `!pip install unsloth` in a fresh runtime |

## Time Estimates

| Setup | T4 (Free) | A100 (Pro) |
|-------|-----------|------------|
| Install + load model | ~5 min | ~3 min |
| DPO training (500 pairs, 2 epochs) | ~20-30 min | ~5-10 min |
| Testing + export | ~5 min | ~3 min |
| **Total** | **~35-45 min** | **~15-20 min** |
