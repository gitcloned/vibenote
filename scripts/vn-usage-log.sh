#!/usr/bin/env bash
# Usage: vn-usage-log.sh <type> <thread> <is_new_thread> <gap_days> <session_dir>
# type: capture | query | think | return | overview | position_update | report
# is_new_thread: true | false
# gap_days: integer or empty string for null
# thread: slug or empty string for null
# session_dir: path or empty string for null

set -e
VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"

TYPE="$1"
THREAD="$2"
IS_NEW="${3:-false}"
GAP_DAYS="$4"
SESSION_DIR="$5"

TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

python3 - <<PYEOF >> "$VIBENOTE_HOME/meta/usage.jsonl"
import json

gap = $( [ -n "$GAP_DAYS" ] && echo "$GAP_DAYS" || echo "None" )
thread = "$THREAD" if "$THREAD" else None
session = "$SESSION_DIR" if "$SESSION_DIR" else None
is_new = True if "$IS_NEW" == "true" else False

event = {
    "ts": "$TS",
    "type": "$TYPE",
    "thread": thread,
    "is_new_thread": is_new,
    "gap_days": gap,
    "session_dir": session
}
print(json.dumps(event, separators=(',', ':')))
PYEOF
