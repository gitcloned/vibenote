/**
 * Seed Firestore with evaluation pairs from your spreadsheet data.
 *
 * Usage:
 *   1. npm install firebase-admin
 *   2. Download a service account key from Firebase Console →
 *      Project Settings → Service Accounts → Generate New Private Key
 *   3. Run: node seed-firestore.js path/to/serviceAccountKey.json
 *
 * This creates documents in the "eval_pairs" collection.
 * Each document has: prompt, level, model_a_name, model_a_response, model_b_name, model_b_response
 *
 * The model names are stored in Firestore but NEVER shown to evaluators until after they vote.
 */

const admin = require('firebase-admin');
const path = require('path');

const keyPath = process.argv[2];
if (!keyPath) {
  console.error('Usage: node seed-firestore.js <path-to-serviceAccountKey.json>');
  process.exit(1);
}

const serviceAccount = require(path.resolve(keyPath));
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});
const db = admin.firestore();

// ─── YOUR EVAL PAIRS ─────────────────────────────────────────────────
// Paste your data here, or read from a JSON/CSV file.
// Format: each pair compares two models on the same prompt.
const evalPairs = [
  {
    prompt: "What is the past tense of 'go'?",
    level: "beginner",
    model_a_name: "fluento-dpo-v1",
    model_a_response: "Good question! Does 'go' follow the normal '-ed' rule? Try saying 'goed' — does that sound right to you?",
    model_b_name: "gemini-flash-2.5",
    model_b_response: "The past tense of 'go' is 'went'. It's an irregular verb, so it doesn't follow the usual '-ed' pattern.",
  },
  {
    prompt: "I goed to the store yesterday.",
    level: "beginner",
    model_a_name: "fluento-dpo-v1",
    model_a_response: "Nice try! 'Goed' is a natural guess, but 'go' is irregular — we say 'went'. Can you try the sentence again with 'went'?",
    model_b_name: "gemini-flash-2.5",
    model_b_response: "Great effort! The past tense of 'go' is 'went', not 'goed'. So it should be 'I went to the store yesterday.' Can you try saying that?",
  },
  // ADD MORE PAIRS HERE — paste from your spreadsheet
  // Each row from the sheet becomes one object in this array.
  //
  // To bulk-import from a CSV file instead, see the loadFromCSV() function below.
];

// ─── OPTIONAL: Load from CSV ─────────────────────────────────────────
// Uncomment and adjust if you want to read from a CSV export of your sheet.
/*
const fs = require('fs');
function loadFromCSV(filepath) {
  const text = fs.readFileSync(filepath, 'utf-8');
  const lines = text.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
  return lines.slice(1).map(line => {
    // Simple CSV parse (doesn't handle quoted commas — use a library for complex CSVs)
    const values = line.split(',');
    return {
      prompt: values[headers.indexOf('prompt')] || '',
      level: values[headers.indexOf('level')] || '',
      model_a_name: 'fluento-dpo-v1',
      model_a_response: values[headers.indexOf('fluento')] || '',
      model_b_name: 'gemini-flash-2.5',
      model_b_response: values[headers.indexOf('gemini')] || '',
    };
  }).filter(p => p.prompt && p.model_a_response && p.model_b_response);
}
// const evalPairs = loadFromCSV('./eval-data.csv');
*/

// ─── SEED ────────────────────────────────────────────────────────────
async function seed() {
  console.log(`Seeding ${evalPairs.length} eval pairs...`);

  const batch = db.batch();
  for (const pair of evalPairs) {
    const ref = db.collection('eval_pairs').doc();
    batch.set(ref, {
      prompt: pair.prompt,
      level: pair.level,
      model_a_name: pair.model_a_name,
      model_a_response: pair.model_a_response,
      model_b_name: pair.model_b_name,
      model_b_response: pair.model_b_response,
      created_at: admin.firestore.FieldValue.serverTimestamp(),
    });
  }

  await batch.commit();
  console.log('Done! Eval pairs seeded to Firestore.');
  process.exit(0);
}

seed().catch(e => { console.error(e); process.exit(1); });
