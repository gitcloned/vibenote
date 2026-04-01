#!/usr/bin/env bash
set -e

VIBENOTE_HOME=$(mktemp -d)
export VIBENOTE_HOME
mkdir -p "$VIBENOTE_HOME/meta"

SCRIPT="$(dirname "$0")/../scripts/vn-usage-log.sh"
LOG="$VIBENOTE_HOME/meta/usage.jsonl"
PASS=0; FAIL=0

check() {
  local desc="$1" condition="$2"
  if eval "$condition"; then
    echo "  PASS: $desc"
    PASS=$((PASS+1))
  else
    echo "  FAIL: $desc"
    FAIL=$((FAIL+1))
  fi
}

touch "$LOG"

# Log a capture event
bash "$SCRIPT" capture slm-local-inference false 0 /Users/test/projects/myapp

echo "=== test-usage-log.sh ==="
check "one line written"    "[ \$(wc -l < '$LOG') -eq 1 ]"
check "has type field"      "grep -q '\"type\":\"capture\"' '$LOG'"
check "has thread field"    "grep -q '\"thread\":\"slm-local-inference\"' '$LOG'"
check "has ts field"        "grep -q '\"ts\":' '$LOG'"
check "valid json"          "python3 -c \"import json,sys; [json.loads(l) for l in open('$LOG') if l.strip()]\""

# Log a second event (no thread)
bash "$SCRIPT" overview "" false "" /Users/test
check "two lines written"   "[ \$(wc -l < '$LOG') -eq 2 ]"

rm -rf "$VIBENOTE_HOME"
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
