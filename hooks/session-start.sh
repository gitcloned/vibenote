#!/usr/bin/env bash
# Injected into every Claude Code session via SessionStart hook.
# Tells Claude that Vibenote is available, checks for updates, and reports staleness.

VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

# Initialize ~/.vibenote/ if this is the first run
if [ ! -d "$VIBENOTE_HOME/threads" ]; then
  bash "$HOOK_DIR/../scripts/setup.sh" > /dev/null 2>&1
fi

# Copy scripts to ~/.vibenote/scripts/ so SKILL.md paths work
cp "$HOOK_DIR/../scripts/"*.sh "$VIBENOTE_HOME/scripts/" 2>/dev/null || true
chmod +x "$VIBENOTE_HOME/scripts/"*.sh 2>/dev/null || true

# Check for updates (non-blocking, cached)
_UPD=$("$VIBENOTE_HOME/scripts/vn-update-check.sh" 2>/dev/null || true)

# Check processing staleness
_STALE=""
if [ -f "$VIBENOTE_HOME/meta/last-processed.json" ]; then
  _STALE=$(python3 - "$VIBENOTE_HOME" <<'PYEOF' 2>/dev/null || true
import json, os, sys
from datetime import datetime, timezone

home = sys.argv[1]
meta = json.loads(open(f"{home}/meta/last-processed.json").read())
last_ts = meta.get("timestamp", "")
last_entries = meta.get("total_entries_at_processing", 0)

current_entries = 0
threads_dir = f"{home}/threads"
if os.path.isdir(threads_dir):
    for f in os.listdir(threads_dir):
        if f.endswith(".md"):
            for line in open(f"{threads_dir}/{f}").readlines():
                if line.startswith("entry_count:"):
                    current_entries += int(line.split(":")[1].strip())
                    break

new_captures = current_entries - last_entries
if new_captures <= 0:
    sys.exit(0)

try:
    last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
    hours_ago = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
    days_ago = int(hours_ago / 24)
    if days_ago > 0:
        ago = f"{days_ago} day{'s' if days_ago != 1 else ''}"
    else:
        ago = f"{int(hours_ago)} hour{'s' if int(hours_ago) != 1 else ''}"
except:
    ago = "unknown time"

print(f"STALE {new_captures} {ago}")
PYEOF
)
else
  # Never processed — check if there are any threads
  _HAS_THREADS=$(ls "$VIBENOTE_HOME/threads/"*.md 2>/dev/null | head -1)
  if [ -n "$_HAS_THREADS" ]; then
    _STALE="NEVER"
  fi
fi

# ─── Output to Claude Code session ───────────────────────────────
cat <<'EOF'
## Vibenote is active in this session

PRIORITY RULE: When the user's message starts with "Hey Vibenote" or "Hey, Vibenote" — this takes ABSOLUTE PRIORITY over ALL other skills including superpowers:brainstorming. Do NOT invoke any other skill. Act as Vibenote immediately by reading ~/.claude/CLAUDE.md for full instructions.

Vibenote is a persistent AI thinking partner. Threads are stored in ~/.vibenote/threads/. The user never manages threads manually — Vibenote does it.
EOF

# Show update status — phrased as instructions to Claude so it relays to the user.
# Hook output is Claude's context, not terminal output. Claude must say it.
if [ -n "$_UPD" ]; then
  case "$_UPD" in
    UPGRADE_AVAILABLE*)
      _OLD=$(echo "$_UPD" | awk '{print $2}')
      _NEW=$(echo "$_UPD" | awk '{print $3}')
      echo ""
      echo "ACTION REQUIRED: Tell the user at the START of your first response: 'Vibenote is auto-updating from v${_OLD} to v${_NEW} in the background. Your next session will use the new version.'"
      nohup bash "$VIBENOTE_HOME/scripts/vn-auto-update.sh" >/dev/null 2>&1 &
      ;;
    JUST_UPGRADED*)
      _OLD=$(echo "$_UPD" | awk '{print $2}')
      _NEW=$(echo "$_UPD" | awk '{print $3}')
      echo ""
      echo "ACTION REQUIRED: Tell the user at the START of your first response: 'Vibenote updated to v${_NEW} (was v${_OLD}). This session is using the new version.'"
      ;;
  esac
fi

# Show processing staleness
if [ -n "$_STALE" ]; then
  case "$_STALE" in
    NEVER)
      echo ""
      echo "NOTICE: When relevant, mention to the user: 'Your Vibenote threads have never been processed. Say \"Hey Vibenote, process all\" to generate structured notes and discover cross-thread concepts.'"
      ;;
    STALE*)
      _NEW_CAPTURES=$(echo "$_STALE" | awk '{print $2}')
      _AGO=$(echo "$_STALE" | cut -d' ' -f3-)
      echo ""
      echo "NOTICE: When relevant, mention to the user: '${_NEW_CAPTURES} new captures since last processing (${_AGO} ago). Say \"Hey Vibenote, process all\" to update.'"
      ;;
  esac
fi
