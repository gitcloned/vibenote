#!/usr/bin/env bash
set -e

VIBENOTE_HOME=$(mktemp -d)
export VIBENOTE_HOME
mkdir -p "$VIBENOTE_HOME/threads"

SCRIPT="$(dirname "$0")/../scripts/vn-thread-state.sh"
PASS=0; FAIL=0

check() {
  local desc="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  PASS: $desc"
    PASS=$((PASS+1))
  else
    echo "  FAIL: $desc (expected='$expected' got='$actual')"
    FAIL=$((FAIL+1))
  fi
}

# Spark: one entry, created < 7 days ago, no conclusion
cat > "$VIBENOTE_HOME/threads/spark-test.md" <<EOF
---
slug: spark-test
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
updated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
conclusion: false
entry_count: 1
---
EOF

# Active: multiple entries, updated < 7 days ago
cat > "$VIBENOTE_HOME/threads/active-test.md" <<EOF
---
slug: active-test
created: $(date -u -v-3d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "3 days ago" +"%Y-%m-%dT%H:%M:%SZ")
updated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
conclusion: false
entry_count: 5
---
EOF

# Paused: updated 15 days ago, no conclusion
PAUSED_DATE=$(date -u -v-15d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "15 days ago" +"%Y-%m-%dT%H:%M:%SZ")
cat > "$VIBENOTE_HOME/threads/paused-test.md" <<EOF
---
slug: paused-test
created: $PAUSED_DATE
updated: $PAUSED_DATE
conclusion: false
entry_count: 3
---
EOF

# Crystallized: has conclusion
cat > "$VIBENOTE_HOME/threads/crystallized-test.md" <<EOF
---
slug: crystallized-test
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
updated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
conclusion: true
entry_count: 4
---
EOF

# Archived: updated > 60 days ago
ARCHIVED_DATE=$(date -u -v-70d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "70 days ago" +"%Y-%m-%dT%H:%M:%SZ")
cat > "$VIBENOTE_HOME/threads/archived-test.md" <<EOF
---
slug: archived-test
created: $ARCHIVED_DATE
updated: $ARCHIVED_DATE
conclusion: false
entry_count: 2
---
EOF

echo "=== test-thread-state.sh ==="
check "spark detected"        "spark"        "$(bash $SCRIPT spark-test)"
check "active detected"       "active"       "$(bash $SCRIPT active-test)"
check "paused detected"       "paused"       "$(bash $SCRIPT paused-test)"
check "crystallized detected" "crystallized" "$(bash $SCRIPT crystallized-test)"
check "archived detected"     "archived"     "$(bash $SCRIPT archived-test)"

rm -rf "$VIBENOTE_HOME"
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
