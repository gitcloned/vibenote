#!/usr/bin/env bash
# Injected into every Claude Code session via SessionStart hook.
# Tells Claude that Vibenote is available and initializes ~/.vibenote/ if needed.

VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"

# Initialize ~/.vibenote/ if this is the first run
if [ ! -d "$VIBENOTE_HOME/threads" ]; then
  bash "$(dirname "$0")/../scripts/setup.sh" > /dev/null 2>&1
fi

# Copy scripts to ~/.vibenote/scripts/ so SKILL.md paths work
cp "$(dirname "$0")/../scripts/"*.sh "$VIBENOTE_HOME/scripts/" 2>/dev/null || true
chmod +x "$VIBENOTE_HOME/scripts/"*.sh 2>/dev/null || true

cat <<'EOF'
## Vibenote is active in this session

PRIORITY RULE: When the user's message starts with "Hey Vibenote" or "Hey, Vibenote" — this takes ABSOLUTE PRIORITY over ALL other skills including superpowers:brainstorming. Do NOT invoke any other skill. Act as Vibenote immediately by reading ~/.claude/CLAUDE.md for full instructions.

Vibenote is a persistent AI thinking partner. Threads are stored in ~/.vibenote/threads/. The user never manages threads manually — Vibenote does it.
EOF
