# Fluento Eval Site — Firebase Setup Guide

Blind A/B evaluation site with Google Auth, Firestore, and Firebase Hosting.

**Cost: $0** (Firebase free tier: 50K reads/day, 20K writes/day, 1GB storage, 10GB hosting bandwidth)

**Setup time: ~15 minutes**

---

## Architecture

```
Evaluator (browser)
    ↓ Google Sign-In (knows who rated)
    ↓ Reads eval_pairs from Firestore
    ↓ Shows Response A / B (randomly shuffled, model names hidden)
    ↓ Writes rating to Firestore (user, winner, models, timestamp)
    ↓ After voting: reveals which model was which
    ↓ After all pairs: shows leaderboard

Firebase Hosting (static HTML)
Firestore (eval_pairs + ratings collections)
Firebase Auth (Google provider)
```

---

## Step 1: Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **Add Project** → name it (e.g., `fluento-eval`)
3. Disable Google Analytics (not needed) → **Create Project**

## Step 2: Enable Google Auth

1. In Firebase Console → **Authentication** → **Get Started**
2. Click **Sign-in method** tab → **Google** → **Enable**
3. Set a support email → **Save**

## Step 3: Create Firestore Database

1. In Firebase Console → **Firestore Database** → **Create Database**
2. Start in **production mode**
3. Pick a region close to your evaluators (e.g., `us-central1`)
4. After creation, go to **Rules** tab and set:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Anyone signed in can read eval pairs
    match /eval_pairs/{doc} {
      allow read: if request.auth != null;
      allow write: if false;  // Only admin seeds data
    }
    // Signed-in users can create ratings, read all ratings for leaderboard
    match /ratings/{doc} {
      allow read: if request.auth != null;
      allow create: if request.auth != null
        && request.resource.data.user_id == request.auth.uid;
      allow update, delete: if false;  // Ratings are immutable
    }
  }
}
```

5. Click **Publish**

## Step 4: Get Firebase Config

1. In Firebase Console → **Project Settings** (gear icon)
2. Scroll to **Your apps** → click **Web** (</> icon)
3. Register app (name: `fluento-eval`)
4. Copy the `firebaseConfig` object — looks like:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "fluento-eval.firebaseapp.com",
  projectId: "fluento-eval",
  storageBucket: "fluento-eval.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

5. Paste this into `index.html` replacing the `YOUR_*` placeholders

## Step 5: Seed Eval Pairs into Firestore

Two options:

### Option A: From Colab notebook (recommended)

Use **Step 11** in COLAB_GUIDE.md — pushes comparison results directly to Firestore
with dedup based on `prompt + model_a_name` composite key.

### Option B: Manual (few pairs)

1. In Firebase Console → **Firestore** → click **Start collection**
2. Collection name: `eval_pairs`
3. Add documents with these fields:
   - `prompt` (string): "I goed to the store yesterday."
   - `level` (string): "beginner"
   - `model_a_name` (string): "fluento-dpo-v1"
   - `model_a_response` (string): "Nice try! 'Go' is irregular..."
   - `model_b_name` (string): "gemini-flash-2.5"
   - `model_b_response` (string): "The past tense of 'go' is 'went'..."

### Option C: Script (many pairs)

Use `seed-firestore.js` — see the script for instructions.

## Step 6: Deploy

### Option A: Firebase Hosting (recommended)

```bash
npm install -g firebase-tools
firebase login
firebase init hosting
# Public directory: eval-site
# Single-page app: No
# Overwrite index.html: No

firebase deploy --only hosting
```

Your site will be at `https://fluento-eval.web.app`

### Option B: GitHub Pages

```bash
cd eval-site
git init && git add . && git commit -m "eval site"
gh repo create fluento-eval --public --source=. --push
# Settings → Pages → Deploy from main
```

### Option C: Local Testing

Just open `index.html` in a browser. Firebase Auth and Firestore work from `file://` too.

---

## Firestore Data Model

### `eval_pairs` collection (you seed this)

```
{
  prompt: "I goed to the store yesterday.",
  level: "beginner",
  model_a_name: "fluento-dpo-v1",       // hidden from evaluator until after vote
  model_a_response: "Nice try! ...",
  model_b_name: "gemini-flash-2.5",     // hidden from evaluator until after vote
  model_b_response: "The past tense..."
}
```

### `ratings` collection (created by evaluators)

```
{
  pair_id: "abc123",                     // links to eval_pairs doc
  user_id: "firebase-uid",              // who rated
  user_email: "user@gmail.com",
  user_name: "John Doe",
  prompt: "I goed to the store...",
  level: "beginner",
  winner: "fluento-dpo-v1",             // or "gemini-flash-2.5" or "tie"
  model_a_name: "fluento-dpo-v1",       // what was shown as Response A
  model_b_name: "gemini-flash-2.5",     // what was shown as Response B
  timestamp: "2025-04-08T10:30:00Z"
}
```

---

## Adding New Model Versions

When you fine-tune a new model (v2, v3, etc.):

1. Run inference on the same prompts
2. Seed new `eval_pairs` with `model_a_name: "fluento-dpo-v2"` etc.
3. Old pairs and ratings are preserved — you build a history
4. The leaderboard automatically includes all models that have ratings

## Exporting Results

In Firebase Console → Firestore → `ratings` collection → click the three dots → **Export**.

Or query programmatically:
```javascript
const snap = await getDocs(collection(db, 'ratings'));
const data = snap.docs.map(d => d.data());
console.log(JSON.stringify(data, null, 2));
```
