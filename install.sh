#!/usr/bin/env bash
# Installs Vibenote as a local Claude Code plugin
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$HOME/.claude/plugins/cache/local/vibenote/1.0.0"
INSTALLED_JSON="$HOME/.claude/plugins/installed_plugins.json"
SETTINGS_JSON="$HOME/.claude/settings.json"

echo "Installing Vibenote..."

# Copy plugin files
mkdir -p "$PLUGIN_ROOT"
cp -r "$SCRIPT_DIR/package.json" "$PLUGIN_ROOT/"
cp -r "$SCRIPT_DIR/skills" "$PLUGIN_ROOT/"
cp -r "$SCRIPT_DIR/hooks" "$PLUGIN_ROOT/"
cp -r "$SCRIPT_DIR/scripts" "$PLUGIN_ROOT/"
chmod +x "$PLUGIN_ROOT/scripts/"*.sh
chmod +x "$PLUGIN_ROOT/hooks/session-start.sh"

# Register in installed_plugins.json
python3 - <<PYEOF
import json, os, datetime

path = os.path.expanduser('$INSTALLED_JSON')
with open(path) as f:
    data = json.load(f)

now = datetime.datetime.utcnow().isoformat() + 'Z'
data.setdefault('plugins', {})['vibenote@local'] = [{
    'scope': 'user',
    'installPath': '$PLUGIN_ROOT',
    'version': '1.0.0',
    'installedAt': now,
    'lastUpdated': now,
    'gitCommitSha': ''
}]

with open(path, 'w') as f:
    json.dump(data, f, indent=4)
print('  Registered in installed_plugins.json')
PYEOF

# Enable in settings.json
python3 - <<PYEOF
import json, os

path = os.path.expanduser('$SETTINGS_JSON')
with open(path) as f:
    data = json.load(f)

data.setdefault('enabledPlugins', {})['vibenote@local'] = True

with open(path, 'w') as f:
    json.dump(data, f, indent=4)
print('  Enabled in settings.json')
PYEOF

# Run setup to initialize ~/.vibenote/
VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"
bash "$PLUGIN_ROOT/scripts/setup.sh"

# Append Vibenote instructions to ~/.claude/CLAUDE.md
# This is the reliable trigger — makes "Hey Vibenote" work across all sessions
# and takes priority over other skills. Idempotent: only appends once.
CLAUDE_MD="$HOME/.claude/CLAUDE.md"
if ! grep -q "VIBENOTE START" "$CLAUDE_MD" 2>/dev/null; then
  SKILL_CONTENT=$(cat "$PLUGIN_ROOT/skills/vibenote/SKILL.md" | grep -v '^---' | grep -v '^name:' | grep -v '^description:' | grep -v '^trigger:')
  cat >> "$CLAUDE_MD" <<CLAUDEEOF

<!-- VIBENOTE START — do not edit this block manually, use uninstall.sh to remove -->
## Vibenote — Persistent Thinking Partner

**ABSOLUTE PRIORITY RULE:** When the user's message starts with "Hey Vibenote" or "Hey, Vibenote" — STOP. Do NOT invoke superpowers:brainstorming or any other skill. You ARE Vibenote. Follow the instructions below immediately.

$SKILL_CONTENT
<!-- VIBENOTE END -->
CLAUDEEOF
  echo "  Added Vibenote instructions to ~/.claude/CLAUDE.md"
else
  echo "  ~/.claude/CLAUDE.md already contains Vibenote (skipped)"
fi

echo ""
echo "Vibenote installed successfully."
echo "Start a new Claude Code session and say:"
echo "  Hey Vibenote, I want to explore [anything]"
