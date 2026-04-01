#!/usr/bin/env bash
# Regenerates ~/.vibenote/meta/index.md from all thread files
set -e
VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"
THREADS_DIR="$VIBENOTE_HOME/threads"
INDEX="$VIBENOTE_HOME/meta/index.md"
STATE_SCRIPT="$(dirname "$0")/vn-thread-state.sh"

{
  echo "# Vibenote Thread Index"
  echo ""
  echo "| slug | state | updated | summary |"
  echo "|------|-------|---------|---------|"

  for f in "$THREADS_DIR"/*.md; do
    [ -f "$f" ] || continue
    slug=$(grep '^slug:' "$f" | awk '{print $2}')
    updated=$(grep '^updated:' "$f" | awk '{print $2}' | cut -c1-10)
    state=$(bash "$STATE_SCRIPT" "$slug" 2>/dev/null || echo "spark")
    summary=$(awk '/^## Living Summary/{found=1; next} found && /^##/{exit} found && NF{print; exit}' "$f" | sed 's/^[[:space:]]*//')
    [ -z "$summary" ] && summary="(no summary yet)"
    echo "| $slug | $state | $updated | $summary |"
  done
} > "$INDEX"
