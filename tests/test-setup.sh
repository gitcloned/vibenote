#!/usr/bin/env bash
set -e

# Use a temp dir to avoid touching real ~/.vibenote during tests
VIBENOTE_HOME=$(mktemp -d)
export VIBENOTE_HOME

PASS=0
FAIL=0

check() {
  local desc="$1"
  local condition="$2"
  if eval "$condition"; then
    echo "  PASS: $desc"
    PASS=$((PASS+1))
  else
    echo "  FAIL: $desc"
    FAIL=$((FAIL+1))
  fi
}

# Run setup against temp dir
bash "$(dirname "$0")/../scripts/setup.sh"

echo "=== test-setup.sh ==="
check "threads/ dir exists"       "[ -d '$VIBENOTE_HOME/threads' ]"
check "meta/ dir exists"          "[ -d '$VIBENOTE_HOME/meta' ]"
check "scripts/ dir exists"       "[ -d '$VIBENOTE_HOME/scripts' ]"
check "meta/index.md created"     "[ -f '$VIBENOTE_HOME/meta/index.md' ]"
check "meta/usage.jsonl created"  "[ -f '$VIBENOTE_HOME/meta/usage.jsonl' ]"
check "memory.md created"         "[ -f '$VIBENOTE_HOME/memory.md' ]"
check "index.md has header"       "grep -q '# Vibenote Thread Index' '$VIBENOTE_HOME/meta/index.md'"

rm -rf "$VIBENOTE_HOME"
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
