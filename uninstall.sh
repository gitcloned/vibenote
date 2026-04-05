#!/usr/bin/env bash
# Uninstalls Vibenote from Claude Code
set -e

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
PLUGIN_ROOT="$CLAUDE_DIR/plugins/cache/local/vibenote/1.0.0"
INSTALLED_JSON="$CLAUDE_DIR/plugins/installed_plugins.json"
SETTINGS_JSON="$CLAUDE_DIR/settings.json"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"

echo "Uninstalling Vibenote..."

# Remove plugin files
if [ -d "$PLUGIN_ROOT" ]; then
  rm -rf "$PLUGIN_ROOT"
  echo "  Removed plugin files"
fi

# Deregister from installed_plugins.json
if [ -f "$INSTALLED_JSON" ]; then
  python3 - <<PYEOF
import json, os
path = os.path.expanduser('$INSTALLED_JSON')
with open(path) as f:
    data = json.load(f)
data.get('plugins', {}).pop('vibenote@local', None)
with open(path, 'w') as f:
    json.dump(data, f, indent=4)
print('  Removed from installed_plugins.json')
PYEOF
fi

# Disable in settings.json
if [ -f "$SETTINGS_JSON" ]; then
  python3 - <<PYEOF
import json, os
path = os.path.expanduser('$SETTINGS_JSON')
with open(path) as f:
    data = json.load(f)
data.get('enabledPlugins', {}).pop('vibenote@local', None)
with open(path, 'w') as f:
    json.dump(data, f, indent=4)
print('  Disabled in settings.json')
PYEOF
fi

# Remove Vibenote block from ~/.claude/CLAUDE.md
if [ -f "$CLAUDE_MD" ] && grep -q "VIBENOTE START" "$CLAUDE_MD"; then
  python3 - <<PYEOF
import re
path = '$CLAUDE_MD'
with open(path) as f:
    content = f.read()
# Remove the Vibenote block including surrounding newlines
cleaned = re.sub(r'\n*<!-- VIBENOTE START.*?VIBENOTE END -->\n*', '\n', content, flags=re.DOTALL)
with open(path, 'w') as f:
    f.write(cleaned)
print('  Removed Vibenote block from ~/.claude/CLAUDE.md')
PYEOF
fi

echo ""
echo "Vibenote uninstalled. Your ~/.vibenote/ threads are preserved."
echo "To also delete your threads: rm -rf ~/.vibenote"
