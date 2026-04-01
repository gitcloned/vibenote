#!/usr/bin/env bash
set -e
VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"
LOGFILE="$VIBENOTE_HOME/meta/usage.jsonl"

[ -f "$LOGFILE" ] || { echo "No usage data yet."; exit 0; }

python3 << 'PYEOF'
import json, os, sys
from datetime import datetime, timezone
from collections import defaultdict, Counter

logfile = os.path.join(os.environ.get('VIBENOTE_HOME', os.path.expanduser('~/.vibenote')), 'meta/usage.jsonl')

events = []
with open(logfile) as f:
    for line in f:
        line = line.strip()
        if line:
            events.append(json.loads(line))

if not events:
    print("No usage data yet.")
    sys.exit(0)

total = len(events)
by_type = Counter(e['type'] for e in events)
threads_touched = set(e['thread'] for e in events if e.get('thread'))
new_threads = sum(1 for e in events if e.get('is_new_thread'))
returns = [e for e in events if e['type'] == 'return']
gap_days_list = [e['gap_days'] for e in returns if e.get('gap_days') is not None]
avg_gap = round(sum(gap_days_list) / len(gap_days_list), 1) if gap_days_list else None

by_week = defaultdict(int)
for e in events:
    try:
        dt = datetime.fromisoformat(e['ts'].replace('Z', '+00:00'))
        week = dt.strftime('%Y-W%W')
        by_week[week] += 1
    except Exception:
        pass

now = datetime.now(timezone.utc)
print(f"=== Vibenote Usage Report ===")
print(f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")
print()
print(f"Total interactions: {total}")
print()
print("By type:")
for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
    print(f"  {t:<20} {c}")
print()
print(f"Threads touched: {len(threads_touched)}")
for t in sorted(threads_touched):
    print(f"  - {t}")
print()
print(f"New threads created: {new_threads}")
print(f"Returns to threads: {len(returns)}")
if avg_gap is not None:
    print(f"Avg gap on returns: {avg_gap} days")
print()
print("Weekly activity:")
for week in sorted(by_week.keys())[-4:]:
    print(f"  {week}: {by_week[week]} interactions")
PYEOF
