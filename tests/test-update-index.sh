#!/usr/bin/env bash
set -e

VIBENOTE_HOME=$(mktemp -d)
export VIBENOTE_HOME
mkdir -p "$VIBENOTE_HOME/threads" "$VIBENOTE_HOME/meta"

SCRIPT="$(dirname "$0")/../scripts/vn-update-index.sh"
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

# Create two threads
cat > "$VIBENOTE_HOME/threads/slm-test.md" <<EOF
---
slug: slm-test
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
updated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
conclusion: false
entry_count: 2
---

## Living Summary
Exploring SLMs locally.
EOF

cat > "$VIBENOTE_HOME/threads/kafka-test.md" <<EOF
---
slug: kafka-test
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
updated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
conclusion: false
entry_count: 1
---

## Living Summary
Thinking about Kafka migration.
EOF

echo "=== test-update-index.sh ==="
bash "$SCRIPT"

check "index.md created"    "[ -f '$VIBENOTE_HOME/meta/index.md' ]"
check "has header"          "grep -q '# Vibenote Thread Index' '$VIBENOTE_HOME/meta/index.md'"
check "slm-test in index"   "grep -q 'slm-test' '$VIBENOTE_HOME/meta/index.md'"
check "kafka-test in index" "grep -q 'kafka-test' '$VIBENOTE_HOME/meta/index.md'"

rm -rf "$VIBENOTE_HOME"
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
