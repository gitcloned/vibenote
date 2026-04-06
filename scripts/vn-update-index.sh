#!/usr/bin/env bash
# Regenerates ~/.vibenote/meta/index.md from all thread files.
# Sorts by updated (most recent first).
set -e
VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"
THREADS_DIR="$VIBENOTE_HOME/threads"
INDEX="$VIBENOTE_HOME/meta/index.md"
STATE_SCRIPT="$(dirname "$0")/vn-thread-state.sh"

# Collect rows into a temp file so we can sort by updated timestamp.
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

for f in "$THREADS_DIR"/*.md; do
  [ -f "$f" ] || continue

  slug=$(grep '^slug:' "$f" | head -1 | awk '{print $2}')
  description=$(grep '^description:' "$f" | head -1 | sed 's/^description: *//')
  updated=$(grep '^updated:' "$f" | head -1 | awk '{print $2}')
  updated_short=$(echo "$updated" | cut -c1-10)
  entries=$(grep '^entry_count:' "$f" | head -1 | awk '{print $2}')
  state=$(bash "$STATE_SCRIPT" "$slug" 2>/dev/null || echo "spark")

  # Use the description field as the summary. Fall back to structured note
  # first-line if no description exists (older threads).
  summary="$description"
  if [ -z "$summary" ]; then
    summary=$(awk '
      /^## Structured Note/ { found=1; next }
      found && /^## / { exit }
      found && /^---$/ { next }
      found && NF {
        gsub(/\*\*/, "")
        gsub(/^\*|\*$/, "")
        print
        exit
      }
    ' "$f")
  fi

  # Truncate long summaries so the table stays readable.
  if [ ${#summary} -gt 100 ]; then
    summary="${summary:0:97}..."
  fi
  [ -z "$summary" ] && summary="(no summary yet)"

  # Mark processed status for quick scanning.
  processed="yes"
  case "$summary" in
    "Not yet processed"*|"Too little content"*) processed="no" ;;
  esac

  # Escape pipes in summary so the markdown table doesn't break.
  summary=$(echo "$summary" | sed 's/|/\\|/g')

  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$updated" "$slug" "$state" "$updated_short" "$entries" "$processed|$summary" >> "$TMP"
done

{
  echo "# Vibenote Thread Index"
  echo ""
  echo "| slug | state | updated | entries | processed | summary |"
  echo "|------|-------|---------|---------|-----------|---------|"

  # Sort by first field (updated, ISO timestamp) descending, then drop it.
  sort -r "$TMP" | while IFS=$'\t' read -r _ slug state updated_short entries rest; do
    processed="${rest%%|*}"
    summary="${rest#*|}"
    echo "| $slug | $state | $updated_short | $entries | $processed | $summary |"
  done
} > "$INDEX"
