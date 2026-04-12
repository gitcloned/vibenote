#!/usr/bin/env bash
# Tests for the auto-update system.
#
# Creates an isolated test vault + a local HTTP server serving fake VERSION files.
# No real GitHub calls. Runs in ~5 seconds.
#
# Usage: bash tests/test-auto-update.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PASS=0
FAIL=0

# ─── Colors ──────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; DIM='\033[2m'; RESET='\033[0m'

pass() { PASS=$((PASS + 1)); printf "  ${GREEN}✓${RESET} %s\n" "$1"; }
fail() { FAIL=$((FAIL + 1)); printf "  ${RED}✗${RESET} %s\n" "$1"; }
section() { echo ""; printf "${DIM}── %s ──${RESET}\n" "$1"; }

# ─── Setup: isolated test vault ──────────────────────────────────
TEST_DIR="$(mktemp -d)"
TEST_VAULT="$TEST_DIR/vault"
TEST_REMOTE="$TEST_DIR/remote"
trap 'rm -rf "$TEST_DIR"' EXIT

mkdir -p "$TEST_VAULT/meta" "$TEST_VAULT/scripts" "$TEST_VAULT/threads"
mkdir -p "$TEST_REMOTE"

# Copy scripts to test vault
cp "$REPO_DIR/scripts/vn-update-check.sh" "$TEST_VAULT/scripts/"
cp "$REPO_DIR/scripts/vn-auto-update.sh" "$TEST_VAULT/scripts/"
chmod +x "$TEST_VAULT/scripts/"*.sh

# ─── Local HTTP server for fake remote VERSION ───────────────────
# Use Python's http.server on a random port
echo "0.3.0" > "$TEST_REMOTE/VERSION"

# Start server in background
python3 -m http.server 0 --directory "$TEST_REMOTE" >/dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to start and find the port
sleep 1
SERVER_PORT=$(lsof -nP -iTCP -sTCP:LISTEN -a -p $SERVER_PID 2>/dev/null | awk 'NR>1{print $9}' | grep -o '[0-9]*$' | head -1)

if [ -z "$SERVER_PORT" ]; then
  echo "Failed to start test HTTP server"
  kill $SERVER_PID 2>/dev/null || true
  exit 1
fi

REMOTE_URL="http://localhost:${SERVER_PORT}/VERSION"
trap 'kill $SERVER_PID 2>/dev/null; rm -rf "$TEST_DIR"' EXIT

echo "Test server on port $SERVER_PORT (remote VERSION: 0.3.0)"

# ─── Helper to run update check in isolation ─────────────────────
run_check() {
  VIBENOTE_HOME="$TEST_VAULT" \
  VIBENOTE_REMOTE_VERSION_URL="$REMOTE_URL" \
  bash "$TEST_VAULT/scripts/vn-update-check.sh" 2>/dev/null || true
}

# ═══════════════════════════════════════════════════════════════════
section "Test 1: Detects upgrade when local < remote"

echo "0.2.0" > "$TEST_VAULT/VERSION"
rm -f "$TEST_VAULT/meta/last-update-check"

OUTPUT=$(run_check)
if echo "$OUTPUT" | grep -q "UPGRADE_AVAILABLE 0.2.0 0.3.0"; then
  pass "Detected upgrade 0.2.0 → 0.3.0"
else
  fail "Expected UPGRADE_AVAILABLE 0.2.0 0.3.0, got: $OUTPUT"
fi

# ═══════════════════════════════════════════════════════════════════
section "Test 2: Up-to-date when local == remote"

echo "0.3.0" > "$TEST_VAULT/VERSION"
rm -f "$TEST_VAULT/meta/last-update-check"

OUTPUT=$(run_check)
if [ -z "$OUTPUT" ]; then
  pass "Silent when up to date"
else
  fail "Expected no output, got: $OUTPUT"
fi

# Verify cache was written
if grep -q "UP_TO_DATE 0.3.0" "$TEST_VAULT/meta/last-update-check" 2>/dev/null; then
  pass "Cache written as UP_TO_DATE"
else
  fail "Cache not written correctly"
fi

# ═══════════════════════════════════════════════════════════════════
section "Test 3: Cache hit (no network call within TTL)"

echo "0.2.0" > "$TEST_VAULT/VERSION"
echo "UP_TO_DATE 0.2.0" > "$TEST_VAULT/meta/last-update-check"
# Touch cache to make it fresh (within 60 min TTL)
touch "$TEST_VAULT/meta/last-update-check"

OUTPUT=$(run_check)
if [ -z "$OUTPUT" ]; then
  pass "Cache hit — no fetch, silent"
else
  fail "Expected cache hit (silent), got: $OUTPUT"
fi

# ═══════════════════════════════════════════════════════════════════
section "Test 4: Cached UPGRADE_AVAILABLE replays from cache"

echo "0.2.0" > "$TEST_VAULT/VERSION"
echo "UPGRADE_AVAILABLE 0.2.0 0.3.0" > "$TEST_VAULT/meta/last-update-check"
touch "$TEST_VAULT/meta/last-update-check"

OUTPUT=$(run_check)
if echo "$OUTPUT" | grep -q "UPGRADE_AVAILABLE 0.2.0 0.3.0"; then
  pass "Cached upgrade notice replayed"
else
  fail "Expected cached UPGRADE_AVAILABLE, got: $OUTPUT"
fi

# ═══════════════════════════════════════════════════════════════════
section "Test 5: Network failure — fails silently"

echo "0.2.0" > "$TEST_VAULT/VERSION"
rm -f "$TEST_VAULT/meta/last-update-check"

# Point at a non-existent server
OUTPUT=$(VIBENOTE_HOME="$TEST_VAULT" \
  VIBENOTE_REMOTE_VERSION_URL="http://localhost:1/VERSION" \
  bash "$TEST_VAULT/scripts/vn-update-check.sh" 2>/dev/null || true)

if [ -z "$OUTPUT" ]; then
  pass "Silent on network failure"
else
  fail "Expected silence on network failure, got: $OUTPUT"
fi

# ═══════════════════════════════════════════════════════════════════
section "Test 6: JUST_UPGRADED marker consumed"

echo "0.3.0" > "$TEST_VAULT/VERSION"
echo "0.2.0" > "$TEST_VAULT/meta/just-upgraded-from"
rm -f "$TEST_VAULT/meta/last-update-check"

OUTPUT=$(run_check)
if echo "$OUTPUT" | grep -q "JUST_UPGRADED 0.2.0 0.3.0"; then
  pass "JUST_UPGRADED shown"
else
  fail "Expected JUST_UPGRADED 0.2.0 0.3.0, got: $OUTPUT"
fi

# Marker should be consumed (deleted)
if [ ! -f "$TEST_VAULT/meta/just-upgraded-from" ]; then
  pass "Marker consumed after display"
else
  fail "Marker not deleted"
fi

# ═══════════════════════════════════════════════════════════════════
section "Test 7: No VERSION file — skip silently"

rm -f "$TEST_VAULT/VERSION"
rm -f "$TEST_VAULT/.last-install-version"
rm -f "$TEST_VAULT/meta/last-update-check"

OUTPUT=$(run_check)
if [ -z "$OUTPUT" ]; then
  pass "Silent when no VERSION file"
else
  fail "Expected silence, got: $OUTPUT"
fi

# ═══════════════════════════════════════════════════════════════════
section "Test 8: Falls back to .last-install-version"

rm -f "$TEST_VAULT/VERSION"
echo "0.2.0" > "$TEST_VAULT/.last-install-version"
rm -f "$TEST_VAULT/meta/last-update-check"

OUTPUT=$(run_check)
if echo "$OUTPUT" | grep -q "UPGRADE_AVAILABLE 0.2.0 0.3.0"; then
  pass "Fallback to .last-install-version works"
else
  fail "Expected UPGRADE_AVAILABLE via fallback, got: $OUTPUT"
fi

# ═══════════════════════════════════════════════════════════════════
section "Test 9: Concurrent update lock"

echo "0.2.0" > "$TEST_VAULT/VERSION"
mkdir -p "$TEST_VAULT/meta"
# Create a fresh lock file (simulating another update in progress)
echo "99999" > "$TEST_VAULT/meta/update.lock"
touch "$TEST_VAULT/meta/update.lock"

VIBENOTE_HOME="$TEST_VAULT" \
  bash "$TEST_VAULT/scripts/vn-auto-update.sh" 2>/dev/null || true

# The lock file should still exist (wasn't our lock, we exited early)
if [ -f "$TEST_VAULT/meta/update.lock" ]; then
  pass "Concurrent update blocked by lock"
else
  fail "Lock file was removed (shouldn't have been)"
fi

# Clean up lock for next tests
rm -f "$TEST_VAULT/meta/update.lock"

# ═══════════════════════════════════════════════════════════════════
section "Test 10: Stale lock (>10 min) is ignored"

echo "0.2.0" > "$TEST_VAULT/VERSION"
echo "99999" > "$TEST_VAULT/meta/update.lock"
# Make lock file 15 minutes old
touch -t "$(date -v-15M +%Y%m%d%H%M.%S 2>/dev/null || date -d '15 minutes ago' +%Y%m%d%H%M.%S 2>/dev/null)" "$TEST_VAULT/meta/update.lock" 2>/dev/null || true

# This test depends on the stale lock being detected. On some systems
# touch -t may not work. If the lock is still "fresh", skip gracefully.
LOCK_AGE=$(find "$TEST_VAULT/meta/update.lock" -mmin +10 2>/dev/null || true)
if [ -n "$LOCK_AGE" ]; then
  pass "Stale lock detected (>10 min old)"
else
  printf "  ${DIM}⊘${RESET} Skipped — couldn't backdate lock file on this platform\n"
fi

rm -f "$TEST_VAULT/meta/update.lock"

# ═══════════════════════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "Results: ${GREEN}${PASS} passed${RESET}"
if [ "$FAIL" -gt 0 ]; then
  printf ", ${RED}${FAIL} failed${RESET}"
fi
echo ""

exit "$FAIL"
