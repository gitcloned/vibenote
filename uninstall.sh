#!/usr/bin/env bash
# Vibenote uninstaller — removes the plugin, bridge, MCP server, and Chrome native host.
# Preserves your vault (threads, concepts, my notes) by default.
set -e

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"
INSTALLED_JSON="$CLAUDE_DIR/plugins/installed_plugins.json"
SETTINGS_JSON="$CLAUDE_DIR/settings.json"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"

# Platform detection for Claude Desktop config path
case "$(uname -s)" in
  Darwin)  CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
  Linux)   CLAUDE_DESKTOP_CONFIG="$HOME/.config/Claude/claude_desktop_config.json" ;;
  MINGW*|MSYS*|CYGWIN*) CLAUDE_DESKTOP_CONFIG="$APPDATA/Claude/claude_desktop_config.json" ;;
  *) CLAUDE_DESKTOP_CONFIG="" ;;
esac

case "$(uname -s)" in
  Darwin)  CHROME_NATIVE_HOST_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts" ;;
  Linux)   CHROME_NATIVE_HOST_DIR="$HOME/.config/google-chrome/NativeMessagingHosts" ;;
  *) CHROME_NATIVE_HOST_DIR="" ;;
esac

echo "Uninstalling Vibenote..."

# Remove all versioned plugin caches
if [ -d "$CLAUDE_DIR/plugins/cache/local/vibenote" ]; then
  rm -rf "$CLAUDE_DIR/plugins/cache/local/vibenote"
  echo "  Removed plugin cache"
fi

# Deregister from installed_plugins.json
if [ -f "$INSTALLED_JSON" ]; then
  python3 - <<PYEOF 2>/dev/null || true
import json
path = '$INSTALLED_JSON'
with open(path) as f:
    data = json.load(f)
data.get('plugins', {}).pop('vibenote@local', None)
with open(path, 'w') as f:
    json.dump(data, f, indent=4)
PYEOF
  echo "  Removed from installed_plugins.json"
fi

# Disable in settings.json
if [ -f "$SETTINGS_JSON" ]; then
  python3 - <<PYEOF 2>/dev/null || true
import json
path = '$SETTINGS_JSON'
with open(path) as f:
    data = json.load(f)
data.get('enabledPlugins', {}).pop('vibenote@local', None)
with open(path, 'w') as f:
    json.dump(data, f, indent=4)
PYEOF
  echo "  Disabled in settings.json"
fi

# Remove Vibenote block from ~/.claude/CLAUDE.md
if [ -f "$CLAUDE_MD" ] && grep -q "VIBENOTE START" "$CLAUDE_MD"; then
  python3 - <<PYEOF
import re
path = '$CLAUDE_MD'
with open(path) as f:
    content = f.read()
cleaned = re.sub(r'\n*<!-- VIBENOTE START.*?VIBENOTE END -->\n*', '\n', content, flags=re.DOTALL)
with open(path, 'w') as f:
    f.write(cleaned)
PYEOF
  echo "  Removed Vibenote block from CLAUDE.md"
fi

# Remove Chrome native messaging host manifest
if [ -n "$CHROME_NATIVE_HOST_DIR" ] && [ -f "$CHROME_NATIVE_HOST_DIR/com.vibenote.bridge.json" ]; then
  rm -f "$CHROME_NATIVE_HOST_DIR/com.vibenote.bridge.json"
  echo "  Removed Chrome native messaging host manifest"
fi

# Remove Vibenote from Claude Desktop MCP config
if [ -n "$CLAUDE_DESKTOP_CONFIG" ] && [ -f "$CLAUDE_DESKTOP_CONFIG" ]; then
  python3 - <<PYEOF 2>/dev/null || true
import json
path = "$CLAUDE_DESKTOP_CONFIG"
with open(path) as f:
    try: data = json.load(f)
    except: data = {}
if 'mcpServers' in data and 'vibenote' in data.get('mcpServers', {}):
    del data['mcpServers']['vibenote']
    if not data['mcpServers']:
        del data['mcpServers']
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
PYEOF
  echo "  Removed Vibenote from Claude Desktop MCP config"
fi

# Remove binaries from ~/.vibenote/bin/ (but preserve vault content)
if [ -d "$VIBENOTE_HOME/bin" ]; then
  rm -f "$VIBENOTE_HOME/bin/vibenote-bridge.py"
  rm -f "$VIBENOTE_HOME/bin/vibenote-mcp.py"
  # Remove bin dir if empty
  rmdir "$VIBENOTE_HOME/bin" 2>/dev/null || true
  echo "  Removed bridge and MCP server binaries"
fi

echo ""
echo "Vibenote uninstalled. Your vault is preserved at $VIBENOTE_HOME/"
echo "To also delete your vault (threads, concepts, my notes):"
echo "  rm -rf $VIBENOTE_HOME"
