#!/usr/bin/env bash
# Usage: vn-thread-state.sh <thread-slug>
# Outputs: spark | active | paused | crystallized | archived

set -e
VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"
SLUG="$1"
FILE="$VIBENOTE_HOME/threads/$SLUG.md"

[ -f "$FILE" ] || { echo "spark"; exit 0; }

# Read frontmatter values
conclusion=$(grep '^conclusion:' "$FILE" | awk '{print $2}')
entry_count=$(grep '^entry_count:' "$FILE" | awk '{print $2}')
updated=$(grep '^updated:' "$FILE" | awk '{print $2}')

# Compute days since last update
now_epoch=$(date -u +%s)
# macOS and Linux date compat
updated_epoch=$(date -u -jf "%Y-%m-%dT%H:%M:%SZ" "$updated" +%s 2>/dev/null \
  || date -u -d "$updated" +%s 2>/dev/null \
  || echo "$now_epoch")
days_ago=$(( (now_epoch - updated_epoch) / 86400 ))

if [ "$conclusion" = "true" ]; then
  echo "crystallized"
elif [ "$days_ago" -gt 60 ]; then
  echo "archived"
elif [ "$days_ago" -gt 7 ]; then
  echo "paused"
elif [ "${entry_count:-1}" -le 1 ]; then
  echo "spark"
else
  echo "active"
fi
