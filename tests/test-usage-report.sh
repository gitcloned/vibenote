#!/usr/bin/env bash
set -e

VIBENOTE_HOME=$(mktemp -d)
export VIBENOTE_HOME
mkdir -p "$VIBENOTE_HOME/meta"
touch "$VIBENOTE_HOME/meta/usage.jsonl"

REPORT_SCRIPT="$(dirname "$0")/../scripts/vn-usage-report.sh"
LOG_SCRIPT="$(dirname "$0")/../scripts/vn-usage-log.sh"
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

# Seed 10 events
bash "$LOG_SCRIPT" capture slm-inference false 0 /projects/app
bash "$LOG_SCRIPT" capture slm-inference false 1 /projects/app
bash "$LOG_SCRIPT" query   slm-inference false 2 /projects/app
bash "$LOG_SCRIPT" capture kafka-migration false 0 /projects/api
bash "$LOG_SCRIPT" think   kafka-migration false 3 /projects/api
bash "$LOG_SCRIPT" return  slm-inference false 5 /projects/app
bash "$LOG_SCRIPT" capture new-idea true "" /
bash "$LOG_SCRIPT" overview "" false "" /
bash "$LOG_SCRIPT" capture kafka-migration false 2 /projects/api
bash "$LOG_SCRIPT" report "" false "" /

REPORT=$(bash "$REPORT_SCRIPT")

echo "=== test-usage-report.sh ==="
check "shows total 10"          "echo \"\$REPORT\" | grep -q 'Total interactions: 10'"
check "shows capture type"      "echo \"\$REPORT\" | grep -qi 'capture'"
check "shows slm-inference"     "echo \"\$REPORT\" | grep -q 'slm-inference'"
check "shows new threads count" "echo \"\$REPORT\" | grep -qi 'new thread'"
check "shows returns"           "echo \"\$REPORT\" | grep -qi 'return'"

rm -rf "$VIBENOTE_HOME"
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
