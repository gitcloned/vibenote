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

# Initialize config.json if not present. Sets defaults that power users can
# override by editing the file directly.
if [ ! -f "$VIBENOTE_HOME/config.json" ]; then
  cat > "$VIBENOTE_HOME/config.json" <<'EOF'
{
  "claude_config_dir": "~/.claude",
  "_doc_claude_config_dir": "Which Claude Code config directory to use when the bridge shells out to `claude -p` for Q&A. Override if you use a non-default install (e.g. '~/.claude-personal'). Tilde is expanded to $HOME.",

  "ask": {
    "timeout_seconds": 45,
    "model": null,
    "_doc_timeout_seconds": "Maximum wall-clock time for a single `ask` query (subprocess + model). Exceeding this returns a timeout error to the client.",
    "_doc_model": "Optional model override passed to `claude --model`. Null uses Claude Code's default."
  }
}
EOF
fi

echo "Vibenote initialized at $VIBENOTE_HOME"
