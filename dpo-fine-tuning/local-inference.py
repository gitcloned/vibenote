"""
Local inference + Gemini comparison.
Downloads fluento-merged from Google Drive first, then runs locally.

Usage:
  1. Download fluento-merged/ folder from Google Drive to ~/fluento-merged
  2. pip install mlx-lm google-generativeai firebase-admin
  3. python local-inference.py --gemini-key YOUR_KEY

Or without Gemini comparison:
  python local-inference.py

Results are written to Firestore (eval_pairs collection).
Duplicate prompts are skipped automatically.
"""

import argparse
import time
import os
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "fluento-merged")
FIREBASE_KEY_PATH = os.path.join(os.path.dirname(__file__), "fluento-firebase-secrets.json")
FIRESTORE_COLLECTION = "eval_pairs"
SYSTEM = (
    "You are Fluento, a friendly English language tutor for voice conversations. "
    "Keep responses short (1-2 sentences), ask guiding questions, and match the learner's level."
)

TEST_PROMPTS = [
    ("beginner",     "What is the past tense of 'go'?"),
    ("beginner",     "I goed to the store yesterday."),
    ("beginner",     "I want to learn English. I am new student."),
    ("intermediate", "Can you explain what a phrasal verb is?"),
    ("intermediate", "She said me that she was coming."),
    ("intermediate", "How do I use 'since' and 'for' with present perfect?"),
    ("advanced",     "I've been learning English for 10 years. Give me something challenging."),
    ("advanced",     "Between you and I, she's going to resign."),
    ("advanced",     "For all intensive purposes, the project is done."),
]


def load_fluento(model_path):
    """Load the merged model using MLX."""
    from mlx_lm import load, generate
    import os

    model_path = os.path.expanduser(model_path)
    print(f"Loading model from {model_path}...")
    start = time.time()
    model, tokenizer = load(model_path)
    print(f"Model loaded in {time.time() - start:.1f}s")
    return model, tokenizer


def ask_fluento(model, tokenizer, prompt, max_tokens=150):
    """Generate a response from the fine-tuned model."""
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]

    chat_prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    sampler = make_sampler(temp=0.7, top_p=0.9)
    start = time.time()
    response = generate(
        model, tokenizer, prompt=chat_prompt,
        max_tokens=max_tokens, sampler=sampler,
    )
    latency = time.time() - start
    return response.strip(), latency


def init_firestore():
    """Initialize Firestore client using the service account key."""
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(cred)
    return firestore.client()


def save_to_firestore(db, level, prompt, fluento_response, gemini_response):
    """Write one eval pair to Firestore, skipping if the prompt already exists."""
    from firebase_admin import firestore as fs

    # Duplicate check: query by prompt field
    existing = db.collection(FIRESTORE_COLLECTION).where("prompt", "==", prompt).limit(1).get()
    if existing:
        print(f"  [Firestore] Skipped (duplicate prompt): {prompt[:60]}...")
        return False

    db.collection(FIRESTORE_COLLECTION).add({
        "prompt": prompt,
        "level": level,
        "model_a_name": "fluento-dpo-v1",
        "model_a_response": fluento_response,
        "model_b_name": "gemini-flash-2.5",
        "model_b_response": gemini_response,
        "created_at": fs.SERVER_TIMESTAMP,
    })
    print(f"  [Firestore] Saved: {prompt[:60]}...")
    return True


def ask_gemini(gemini_model, prompt, level):
    """Generate a response from Gemini Flash 2.5."""
    start = time.time()
    resp = gemini_model.generate_content(
        f"{SYSTEM}\n\nStudent ({level} level): {prompt}"
    ).text.strip()
    latency = time.time() - start
    return resp, latency


def main():
    parser = argparse.ArgumentParser(description="Fluento local inference + Gemini comparison")
    parser.add_argument("--model-path", default=MODEL_PATH, help="Path to fluento-merged model")
    parser.add_argument("--gemini-key", default=None, help="Gemini API key (optional, skips comparison if not set)")
    parser.add_argument("--prompt", default=None, help="Single prompt to test (interactive mode)")
    parser.add_argument("--no-firestore", action="store_true", help="Skip writing results to Firestore")
    args = parser.parse_args()

    # Init Firestore
    db = None
    if not args.no_firestore and os.path.exists(FIREBASE_KEY_PATH):
        db = init_firestore()
        print("Firestore connected.")
    elif not args.no_firestore:
        print(f"WARNING: Firebase key not found at {FIREBASE_KEY_PATH} — skipping Firestore writes.")

    # Load Fluento
    model, tokenizer = load_fluento(args.model_path)

    # Load Gemini if key provided (arg > env var)
    gemini_model = None
    gemini_key = args.gemini_key or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        print("Gemini Flash 2.5 configured!")

    # Interactive mode
    if args.prompt:
        resp, latency = ask_fluento(model, tokenizer, args.prompt)
        print(f"\nFLUENTO ({latency:.1f}s): {resp}")
        g_resp = ""
        if gemini_model:
            g_resp, g_latency = ask_gemini(gemini_model, args.prompt, "intermediate")
            print(f"GEMINI  ({g_latency:.1f}s): {g_resp}")
        if db:
            save_to_firestore(db, "intermediate", args.prompt, resp, g_resp)
        return

    # Batch comparison
    results = []
    for level, prompt in TEST_PROMPTS:
        f_resp, f_latency = ask_fluento(model, tokenizer, prompt)

        g_resp, g_latency = "", 0
        if gemini_model:
            g_resp, g_latency = ask_gemini(gemini_model, prompt, level)

        results.append((level, prompt, f_resp, f_latency, g_resp, g_latency))

        print(f"\n{'='*70}")
        print(f"[{level.upper()}] STUDENT: {prompt}")
        print(f"\n  FLUENTO ({f_latency:.1f}s): {f_resp}")
        if gemini_model:
            print(f"\n  GEMINI  ({g_latency:.1f}s): {g_resp}")
        if db:
            save_to_firestore(db, level, prompt, f_resp, g_resp)

    # Scorecard
    print(f"\n{'='*70}")
    print("SCORECARD")
    print(f"{'='*70}")

    f_lengths = [len(r[2]) for r in results]
    f_latencies = [r[3] for r in results]
    f_questions = sum(1 for r in results if '?' in r[2])
    f_short = sum(1 for r in results if len(r[2]) < 200)

    print(f"\n{'Metric':<25} {'Fluento (local)':<20}", end="")
    if gemini_model:
        g_lengths = [len(r[4]) for r in results]
        g_latencies = [r[5] for r in results]
        g_questions = sum(1 for r in results if '?' in r[4])
        g_short = sum(1 for r in results if len(r[4]) < 200)
        print(f"{'Gemini Flash 2.5':<20}", end="")
    print()
    print("-" * 65)

    print(f"{'Avg response length':<25} {sum(f_lengths)//len(f_lengths):<20}", end="")
    if gemini_model:
        print(f"{sum(g_lengths)//len(g_lengths):<20}", end="")
    print()

    print(f"{'Avg latency':<25} {sum(f_latencies)/len(f_latencies):.1f}s{'':<15}", end="")
    if gemini_model:
        print(f"{sum(g_latencies)/len(g_latencies):.1f}s{'':<15}", end="")
    print()

    print(f"{'Asks a question':<25} {f_questions}/{len(results):<17}", end="")
    if gemini_model:
        print(f"{g_questions}/{len(results):<17}", end="")
    print()

    print(f"{'Voice-friendly (<200ch)':<25} {f_short}/{len(results):<17}", end="")
    if gemini_model:
        print(f"{g_short}/{len(results):<17}", end="")
    print()


if __name__ == "__main__":
    main()
