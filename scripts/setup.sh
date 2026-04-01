#!/usr/bin/env bash
set -e

VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"

mkdir -p "$VIBENOTE_HOME/threads"
mkdir -p "$VIBENOTE_HOME/meta"
mkdir -p "$VIBENOTE_HOME/scripts"

# Initialize index if not present
if [ ! -f "$VIBENOTE_HOME/meta/index.md" ]; then
  cat > "$VIBENOTE_HOME/meta/index.md" <<'EOF'
# Vibenote Thread Index

| slug | state | updated | summary |
|------|-------|---------|---------|
EOF
fi

# Initialize usage log if not present
if [ ! -f "$VIBENOTE_HOME/meta/usage.jsonl" ]; then
  touch "$VIBENOTE_HOME/meta/usage.jsonl"
fi

# Initialize memory if not present
if [ ! -f "$VIBENOTE_HOME/memory.md" ]; then
  cat > "$VIBENOTE_HOME/memory.md" <<'EOF'
# Vibenote Memory

Cross-thread understanding of the user. Updated by Vibenote over time.
EOF
fi

echo "Vibenote initialized at $VIBENOTE_HOME"
