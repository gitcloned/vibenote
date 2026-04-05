#!/usr/bin/env bash
# Installs Vibenote as a local Claude Code plugin
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
PLUGIN_ROOT="$CLAUDE_DIR/plugins/cache/local/vibenote/1.0.0"
INSTALLED_JSON="$CLAUDE_DIR/plugins/installed_plugins.json"
SETTINGS_JSON="$CLAUDE_DIR/settings.json"

echo "Installing Vibenote..."

# Copy plugin files
mkdir -p "$PLUGIN_ROOT"
cp -r "$SCRIPT_DIR/package.json" "$PLUGIN_ROOT/"
cp -r "$SCRIPT_DIR/skills" "$PLUGIN_ROOT/"
cp -r "$SCRIPT_DIR/hooks" "$PLUGIN_ROOT/"
cp -r "$SCRIPT_DIR/scripts" "$PLUGIN_ROOT/"
if [ -d "$SCRIPT_DIR/bridge" ]; then
  cp -r "$SCRIPT_DIR/bridge" "$PLUGIN_ROOT/"
fi
chmod +x "$PLUGIN_ROOT/scripts/"*.sh
chmod +x "$PLUGIN_ROOT/hooks/session-start.sh"
if [ -f "$PLUGIN_ROOT/bridge/vibenote-bridge.py" ]; then
  chmod +x "$PLUGIN_ROOT/bridge/vibenote-bridge.py"
fi

# Register in installed_plugins.json
python3 - <<PYEOF
import json, os, datetime

path = os.path.expanduser('$INSTALLED_JSON')
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
else:
    data = {}

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

# Mirror scripts into ~/.vibenote/scripts/ so instructions can reference a
# stable, version-less path without knowing the plugin cache location.
mkdir -p "$VIBENOTE_HOME/scripts"
cp "$PLUGIN_ROOT/scripts/"*.sh "$VIBENOTE_HOME/scripts/"
chmod +x "$VIBENOTE_HOME/scripts/"*.sh
echo "  Mirrored scripts into $VIBENOTE_HOME/scripts/"

# Install the native messaging bridge (used by the Chrome extension).
if [ -f "$PLUGIN_ROOT/bridge/vibenote-bridge.py" ]; then
  mkdir -p "$VIBENOTE_HOME/bin"
  cp "$PLUGIN_ROOT/bridge/vibenote-bridge.py" "$VIBENOTE_HOME/bin/"
  chmod +x "$VIBENOTE_HOME/bin/vibenote-bridge.py"
  echo "  Installed native messaging bridge at $VIBENOTE_HOME/bin/vibenote-bridge.py"

  # Register the native messaging host manifest with Chrome (macOS path).
  # The extension ID is a placeholder that gets replaced after dev-loading the
  # extension via vn-link-extension.sh, or set directly for Web Store installs.
  NATIVE_HOST_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
  if [ -d "$HOME/Library/Application Support/Google/Chrome" ] || [ -d "$HOME/Library/Application Support/Google" ]; then
    mkdir -p "$NATIVE_HOST_DIR"
    cat > "$NATIVE_HOST_DIR/com.vibenote.bridge.json" <<NHEOF
{
  "name": "com.vibenote.bridge",
  "description": "Vibenote native messaging bridge",
  "path": "$VIBENOTE_HOME/bin/vibenote-bridge.py",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://__EXTENSION_ID_PLACEHOLDER__/"
  ]
}
NHEOF
    echo "  Registered Chrome native messaging host"
    echo "  (run vn-link-extension.sh <id> after loading the extension to link it)"
  fi
fi

# Append Vibenote instructions to ~/.claude/CLAUDE.md
# This is the reliable trigger — makes "Hey Vibenote" work across all sessions
# and takes priority over other skills. Idempotent: only appends once.
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
if ! grep -q "VIBENOTE START" "$CLAUDE_MD" 2>/dev/null; then
  # Strip only the leading YAML frontmatter block (first --- to second ---),
  # preserving any --- markers inside code-block examples later in the file.
  SKILL_CONTENT=$(awk 'NR==1 && /^---$/ {in_fm=1; next} in_fm && /^---$/ {in_fm=0; next} !in_fm' "$PLUGIN_ROOT/skills/vibenote/SKILL.md")
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
