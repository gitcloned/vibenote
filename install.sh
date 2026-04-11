#!/usr/bin/env bash
# Vibenote installer — sets up vault, Claude Code plugin, bridge, MCP server.
# Idempotent: safe to re-run. Auto-detects available integrations.
#
# Run locally:
#   ./install.sh
#
# Run remotely (curl | bash):
#   curl -fsSL https://raw.githubusercontent.com/gitcloned/vibenote/main/install.sh | bash
#
# When run remotely, this script downloads the repo tarball to a temp dir
# and proceeds with install from there.
set -e

# Determine the script's directory. When run via `curl | bash`, BASH_SOURCE
# may be empty or point to /dev/stdin, so we detect that and fetch the repo.
REPO_URL="https://github.com/gitcloned/vibenote"
VIBENOTE_BRANCH="${VIBENOTE_BRANCH:-main}"
TARBALL_URL="${REPO_URL}/archive/refs/heads/${VIBENOTE_BRANCH}.tar.gz"

detect_script_dir() {
  local src="${BASH_SOURCE[0]:-}"
  if [ -z "$src" ] || [ ! -f "$src" ]; then
    echo ""
    return
  fi
  (cd "$(dirname "$src")" && pwd)
}

SCRIPT_DIR="$(detect_script_dir)"

# If we can't find a local VERSION file next to the script, we're running
# remotely (via curl | bash) and need to fetch the repo.
if [ -z "$SCRIPT_DIR" ] || [ ! -f "$SCRIPT_DIR/VERSION" ]; then
  echo "Fetching Vibenote repo (running remotely)..."
  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT
  if ! curl -fsSL "$TARBALL_URL" | tar xz -C "$TMPDIR"; then
    echo "Error: failed to download Vibenote from $TARBALL_URL" >&2
    echo "Check your network connection or try the manual install:" >&2
    echo "  git clone $REPO_URL && cd vibenote && ./install.sh" >&2
    exit 1
  fi
  # GitHub tarballs extract to a directory like vibenote-<branch>/
  # (GitHub replaces `/` with `-` in branch names, so feat/cross-references → vibenote-feat-cross-references)
  SCRIPT_DIR="$(find "$TMPDIR" -maxdepth 1 -type d -name 'vibenote-*' ! -name 'vibenote-install*' | head -1)"
  if [ -z "$SCRIPT_DIR" ] || [ ! -f "$SCRIPT_DIR/VERSION" ]; then
    echo "Error: fetched repo does not look like Vibenote" >&2
    exit 1
  fi
  echo "  ✓ Downloaded to $SCRIPT_DIR"
  echo ""
fi

VERSION="$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "0.1.0")"

# ─── Colors ──────────────────────────────────────────────────────────
if [ -t 1 ]; then
  CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
  RED='\033[0;31m'; DIM='\033[2m'; BOLD='\033[1m'; RESET='\033[0m'
else
  CYAN=''; GREEN=''; YELLOW=''; RED=''; DIM=''; BOLD=''; RESET=''
fi

section() { echo ""; printf "${BOLD}${CYAN}%s${RESET}\n" "$1"; }
ok()      { printf "  ${GREEN}✓${RESET} %s\n" "$1"; }
warn()    { printf "  ${YELLOW}⚠${RESET}  %s\n" "$1"; }
fail()    { printf "  ${RED}✗${RESET} %s\n" "$1" >&2; }
info()    { printf "  ${DIM}•${RESET} %s\n" "$1"; }

printf "${BOLD}${CYAN}Vibenote installer${RESET} ${DIM}v${VERSION}${RESET}\n"
printf "${DIM}================================${RESET}\n"

# ─── Platform detection ──────────────────────────────────────────────
PLATFORM="unknown"
case "$(uname -s)" in
  Darwin) PLATFORM="macos" ;;
  Linux)  PLATFORM="linux" ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT) PLATFORM="windows" ;;
esac

# ─── Paths ───────────────────────────────────────────────────────────
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
PLUGIN_ROOT="$CLAUDE_DIR/plugins/cache/local/vibenote/$VERSION"
INSTALLED_JSON="$CLAUDE_DIR/plugins/installed_plugins.json"
SETTINGS_JSON="$CLAUDE_DIR/settings.json"
VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"

CLAUDE_DESKTOP_CONFIG=""
case "$PLATFORM" in
  macos)   CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
  linux)   CLAUDE_DESKTOP_CONFIG="$HOME/.config/Claude/claude_desktop_config.json" ;;
  windows) CLAUDE_DESKTOP_CONFIG="$APPDATA/Claude/claude_desktop_config.json" ;;
esac

CHROME_NATIVE_HOST_DIR=""
case "$PLATFORM" in
  macos)   CHROME_NATIVE_HOST_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts" ;;
  linux)   CHROME_NATIVE_HOST_DIR="$HOME/.config/google-chrome/NativeMessagingHosts" ;;
esac

# ─── Flags ───────────────────────────────────────────────────────────
SKIP_PREREQ=0
QUIET=0
while [ $# -gt 0 ]; do
  case "$1" in
    --skip-prereq-check) SKIP_PREREQ=1; shift ;;
    --quiet) QUIET=1; shift ;;
    -h|--help)
      echo "Usage: $0 [--skip-prereq-check] [--quiet]"
      echo ""
      echo "Environment variables:"
      echo "  VIBENOTE_HOME      Vault location (default: ~/.vibenote)"
      echo "  CLAUDE_CONFIG_DIR  Claude Code config dir (default: ~/.claude)"
      exit 0
      ;;
    *) warn "Unknown flag: $1"; shift ;;
  esac
done

# ─── Step 1: Prerequisites ───────────────────────────────────────────
section "Checking prerequisites"

info "Platform: $PLATFORM"

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
  PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
  ok "Python 3 found ($PY_VERSION)"
else
  fail "Python 3 is required but not found"
  echo ""
  echo "  Install Python 3:"
  echo "    macOS:   brew install python3"
  echo "    Linux:   apt install python3  (or equivalent)"
  echo "    Windows: https://python.org/downloads/"
  exit 1
fi

# Claude Code detection
HAS_CLAUDE_CODE=0
if [ -d "$CLAUDE_DIR" ]; then
  HAS_CLAUDE_CODE=1
  ok "Claude Code config found at $CLAUDE_DIR"
else
  warn "Claude Code config directory not found at $CLAUDE_DIR"
  info "The Claude Code skill won't work, but the extension and MCP server will still install."
fi

# Chrome detection (for extension native messaging host)
HAS_CHROME=0
case "$PLATFORM" in
  macos)
    if [ -d "$HOME/Library/Application Support/Google/Chrome" ] || [ -d "/Applications/Google Chrome.app" ]; then
      HAS_CHROME=1
    fi
    ;;
  linux)
    if [ -d "$HOME/.config/google-chrome" ] || command -v google-chrome >/dev/null 2>&1; then
      HAS_CHROME=1
    fi
    ;;
esac
if [ "$HAS_CHROME" -eq 1 ]; then
  ok "Chrome detected (browser extension will be available)"
else
  info "Chrome not detected (browser extension setup will be skipped)"
fi

# Claude Desktop detection
HAS_CLAUDE_DESKTOP=0
if [ -n "$CLAUDE_DESKTOP_CONFIG" ]; then
  CLAUDE_DESKTOP_DIR="$(dirname "$CLAUDE_DESKTOP_CONFIG")"
  if [ -d "$CLAUDE_DESKTOP_DIR" ] || [ -d "/Applications/Claude.app" ]; then
    HAS_CLAUDE_DESKTOP=1
    ok "Claude Desktop detected (MCP integration will be configured)"
  else
    info "Claude Desktop not detected (MCP config will be skipped)"
  fi
fi

# ─── Step 2: Initialize vault ────────────────────────────────────────
section "Initializing vault"

mkdir -p "$VIBENOTE_HOME/threads"
mkdir -p "$VIBENOTE_HOME/concepts/archived"
mkdir -p "$VIBENOTE_HOME/meta"
mkdir -p "$VIBENOTE_HOME/scripts"
mkdir -p "$VIBENOTE_HOME/bin"

if [ ! -f "$VIBENOTE_HOME/meta/index.md" ]; then
  cat > "$VIBENOTE_HOME/meta/index.md" <<'EOF'
# Vibenote Thread Index

| slug | state | updated | entries | processed | summary |
|------|-------|---------|---------|-----------|---------|
EOF
  ok "Created empty thread index"
fi

if [ ! -f "$VIBENOTE_HOME/meta/usage.jsonl" ]; then
  touch "$VIBENOTE_HOME/meta/usage.jsonl"
fi

if [ ! -f "$VIBENOTE_HOME/memory.md" ]; then
  cat > "$VIBENOTE_HOME/memory.md" <<'EOF'
# Vibenote Memory

Cross-thread understanding of the user. Updated by Vibenote over time.
EOF
fi

if [ ! -f "$VIBENOTE_HOME/config.json" ]; then
  cat > "$VIBENOTE_HOME/config.json" <<'EOF'
{
  "claude_config_dir": "~/.claude",
  "_doc_claude_config_dir": "Which Claude Code config directory to use when the bridge shells out to `claude -p`. Override if you use a non-default install (e.g. '~/.claude-personal'). Tilde is expanded to $HOME.",

  "ask": {
    "timeout_seconds": 45,
    "model": null,
    "_doc_timeout_seconds": "Maximum wall-clock time for a single `ask` query.",
    "_doc_model": "Optional model override passed to `claude --model`. Null uses Claude Code's default."
  }
}
EOF
  ok "Created config at $VIBENOTE_HOME/config.json"
else
  info "Config exists at $VIBENOTE_HOME/config.json (preserved)"
fi

ok "Vault at $VIBENOTE_HOME"

# ─── Step 3: Install Claude Code plugin (if Claude Code is present) ──
if [ "$HAS_CLAUDE_CODE" -eq 1 ]; then
  section "Installing Claude Code plugin"

  mkdir -p "$PLUGIN_ROOT"
  cp -r "$SCRIPT_DIR/package.json" "$PLUGIN_ROOT/" 2>/dev/null || true
  cp -r "$SCRIPT_DIR/skills" "$PLUGIN_ROOT/"
  cp -r "$SCRIPT_DIR/hooks" "$PLUGIN_ROOT/"
  cp -r "$SCRIPT_DIR/scripts" "$PLUGIN_ROOT/"
  [ -d "$SCRIPT_DIR/bridge" ] && cp -r "$SCRIPT_DIR/bridge" "$PLUGIN_ROOT/"
  [ -d "$SCRIPT_DIR/mcp" ] && cp -r "$SCRIPT_DIR/mcp" "$PLUGIN_ROOT/"
  chmod +x "$PLUGIN_ROOT/scripts/"*.sh 2>/dev/null || true
  chmod +x "$PLUGIN_ROOT/hooks/session-start.sh" 2>/dev/null || true
  [ -f "$PLUGIN_ROOT/bridge/vibenote-bridge.py" ] && chmod +x "$PLUGIN_ROOT/bridge/vibenote-bridge.py"
  [ -f "$PLUGIN_ROOT/mcp/vibenote-mcp.py" ] && chmod +x "$PLUGIN_ROOT/mcp/vibenote-mcp.py"
  ok "Copied plugin files to $PLUGIN_ROOT"

  # Register in installed_plugins.json (idempotent)
  $PYTHON_BIN - <<PYEOF
import json, os, datetime
path = os.path.expanduser('$INSTALLED_JSON')
data = {}
if os.path.exists(path):
    with open(path) as f:
        try: data = json.load(f)
        except: data = {}
now = datetime.datetime.utcnow().isoformat() + 'Z'
data.setdefault('plugins', {})['vibenote@local'] = [{
    'scope': 'user',
    'installPath': '$PLUGIN_ROOT',
    'version': '$VERSION',
    'installedAt': now,
    'lastUpdated': now,
    'gitCommitSha': ''
}]
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w') as f:
    json.dump(data, f, indent=4)
PYEOF
  ok "Registered in installed_plugins.json"

  # Enable in settings.json
  if [ -f "$SETTINGS_JSON" ]; then
    $PYTHON_BIN - <<PYEOF
import json, os
path = os.path.expanduser('$SETTINGS_JSON')
with open(path) as f:
    data = json.load(f)
data.setdefault('enabledPlugins', {})['vibenote@local'] = True
with open(path, 'w') as f:
    json.dump(data, f, indent=4)
PYEOF
    ok "Enabled in settings.json"
  fi

  # Append Vibenote instructions to CLAUDE.md (idempotent)
  CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
  if ! grep -q "VIBENOTE START" "$CLAUDE_MD" 2>/dev/null; then
    SKILL_CONTENT=$(awk 'NR==1 && /^---$/ {in_fm=1; next} in_fm && /^---$/ {in_fm=0; next} !in_fm' "$PLUGIN_ROOT/skills/vibenote/SKILL.md")
    cat >> "$CLAUDE_MD" <<CLAUDEEOF

<!-- VIBENOTE START — do not edit this block manually, use uninstall.sh to remove -->
## Vibenote — Persistent Thinking Partner

**ABSOLUTE PRIORITY RULE:** When the user's message starts with "Hey Vibenote" or "Hey, Vibenote" — STOP. Do NOT invoke superpowers:brainstorming or any other skill. You ARE Vibenote. Follow the instructions below immediately.

$SKILL_CONTENT
<!-- VIBENOTE END -->
CLAUDEEOF
    ok "Added Vibenote skill to $CLAUDE_MD"
  else
    info "Skill already present in CLAUDE.md (preserved)"
  fi
fi

# ─── Step 4: Install helper scripts into vault ───────────────────────
section "Installing vault scripts"

if [ "$HAS_CLAUDE_CODE" -eq 1 ]; then
  cp "$PLUGIN_ROOT/scripts/"*.sh "$VIBENOTE_HOME/scripts/" 2>/dev/null || true
else
  cp "$SCRIPT_DIR/scripts/"*.sh "$VIBENOTE_HOME/scripts/" 2>/dev/null || true
fi
chmod +x "$VIBENOTE_HOME/scripts/"*.sh 2>/dev/null || true
ok "Helper scripts mirrored to $VIBENOTE_HOME/scripts/"

# ─── Step 5: Install native messaging bridge ─────────────────────────
section "Installing native messaging bridge"

BRIDGE_SRC="$SCRIPT_DIR/bridge/vibenote-bridge.py"
if [ -f "$BRIDGE_SRC" ]; then
  cp "$BRIDGE_SRC" "$VIBENOTE_HOME/bin/"
  chmod +x "$VIBENOTE_HOME/bin/vibenote-bridge.py"
  ok "Bridge installed at $VIBENOTE_HOME/bin/vibenote-bridge.py"

  # Register Chrome native messaging host manifest (idempotent)
  if [ "$HAS_CHROME" -eq 1 ] && [ -n "$CHROME_NATIVE_HOST_DIR" ]; then
    mkdir -p "$CHROME_NATIVE_HOST_DIR"
    cat > "$CHROME_NATIVE_HOST_DIR/com.vibenote.bridge.json" <<NHEOF
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
    ok "Chrome native messaging host registered"
    info "(Run ~/.vibenote/scripts/vn-link-extension.sh <id> after loading the extension)"
  fi
else
  warn "Bridge source not found at $BRIDGE_SRC — skipping"
fi

# ─── Step 6: Install MCP server ──────────────────────────────────────
section "Installing MCP server"

MCP_SRC="$SCRIPT_DIR/mcp/vibenote-mcp.py"
if [ -f "$MCP_SRC" ]; then
  cp "$MCP_SRC" "$VIBENOTE_HOME/bin/"
  chmod +x "$VIBENOTE_HOME/bin/vibenote-mcp.py"
  ok "MCP server installed at $VIBENOTE_HOME/bin/vibenote-mcp.py"

  # Inject into Claude Desktop config (idempotent merge)
  if [ "$HAS_CLAUDE_DESKTOP" -eq 1 ]; then
    mkdir -p "$(dirname "$CLAUDE_DESKTOP_CONFIG")"
    if [ ! -f "$CLAUDE_DESKTOP_CONFIG" ]; then
      echo '{}' > "$CLAUDE_DESKTOP_CONFIG"
    fi
    $PYTHON_BIN - <<PYEOF
import json, os
path = "$CLAUDE_DESKTOP_CONFIG"
with open(path) as f:
    try: data = json.load(f)
    except: data = {}
data.setdefault('mcpServers', {})['vibenote'] = {
    'command': 'python3',
    'args': ['$VIBENOTE_HOME/bin/vibenote-mcp.py'],
    'env': {'VIBENOTE_HOME': '$VIBENOTE_HOME'}
}
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
PYEOF
    ok "Added 'vibenote' to Claude Desktop MCP config"
    info "Restart Claude Desktop to load the new MCP server"
  fi
else
  warn "MCP server source not found at $MCP_SRC — skipping"
fi

# ─── Step 7: Verification ────────────────────────────────────────────
section "Verifying install"

# Check critical files exist
VERIFY_OK=1
for f in \
  "$VIBENOTE_HOME/meta/index.md" \
  "$VIBENOTE_HOME/config.json" \
  "$VIBENOTE_HOME/scripts/vn-update-index.sh"; do
  if [ -f "$f" ]; then
    ok "$(basename "$f") present"
  else
    fail "Missing: $f"
    VERIFY_OK=0
  fi
done

if [ -f "$VIBENOTE_HOME/bin/vibenote-bridge.py" ]; then
  ok "Bridge present"
  # Try a ping
  PING_RESULT=$($PYTHON_BIN - <<PYEOF 2>/dev/null || echo "FAIL"
import subprocess, json, struct, os
msg = json.dumps({'op': 'ping'}).encode()
r = subprocess.run(
    ['$VIBENOTE_HOME/bin/vibenote-bridge.py'],
    input=struct.pack('<I', len(msg)) + msg,
    capture_output=True, timeout=5,
    env={'HOME': os.environ['HOME'], 'PATH': '/usr/bin:/bin'},
)
if r.returncode == 0 and len(r.stdout) > 4:
    length = struct.unpack('<I', r.stdout[:4])[0]
    resp = json.loads(r.stdout[4:4+length])
    if resp.get('ok'): print('PASS')
    else: print('FAIL')
else:
    print('FAIL')
PYEOF
)
  if [ "$PING_RESULT" = "PASS" ]; then
    ok "Bridge responds to ping"
  else
    warn "Bridge installed but ping failed (may still work)"
  fi
fi

if [ -f "$VIBENOTE_HOME/bin/vibenote-mcp.py" ]; then
  ok "MCP server present"
fi

# ─── Step 8: Version marker and welcome ──────────────────────────────
echo "$VERSION" > "$VIBENOTE_HOME/.last-install-version"

FIRST_INSTALL=0
if [ ! -f "$VIBENOTE_HOME/.welcome-seen" ]; then
  FIRST_INSTALL=1
  touch "$VIBENOTE_HOME/.welcome-seen"
fi

# ─── Done ────────────────────────────────────────────────────────────
section "Vibenote installed"

printf "  Vault:  ${DIM}$VIBENOTE_HOME${RESET}\n"
[ "$HAS_CLAUDE_CODE" -eq 1 ] && printf "  Claude Code: ${GREEN}✓${RESET}  ${DIM}skill installed${RESET}\n"
[ "$HAS_CHROME" -eq 1 ] && printf "  Chrome:      ${GREEN}✓${RESET}  ${DIM}native host registered${RESET}\n"
[ "$HAS_CLAUDE_DESKTOP" -eq 1 ] && printf "  Claude Desktop: ${GREEN}✓${RESET}  ${DIM}MCP server configured${RESET}\n"

echo ""
if [ "$FIRST_INSTALL" -eq 1 ]; then
  printf "${BOLD}Next steps:${RESET}\n"
  echo ""
  if [ "$HAS_CLAUDE_CODE" -eq 1 ]; then
    printf "  ${CYAN}1.${RESET} Start a new Claude Code session and say:\n"
    printf "     ${DIM}Hey Vibenote, this is my first capture${RESET}\n"
    echo ""
  fi
  if [ "$HAS_CLAUDE_DESKTOP" -eq 1 ]; then
    printf "  ${CYAN}2.${RESET} Restart Claude Desktop, then ask:\n"
    printf "     ${DIM}What's in my Vibenote vault?${RESET}\n"
    echo ""
  fi
  if [ "$HAS_CHROME" -eq 1 ]; then
    printf "  ${CYAN}3.${RESET} Install the Chrome extension (optional):\n"
    printf "     ${DIM}a. Open chrome://extensions, enable Developer mode${RESET}\n"
    printf "     ${DIM}b. Load unpacked: $SCRIPT_DIR/extension${RESET}\n"
    printf "     ${DIM}c. Run: bash $VIBENOTE_HOME/scripts/vn-link-extension.sh <id>${RESET}\n"
    echo ""
  fi
  printf "  ${DIM}Docs: https://github.com/gitcloned/vibenote${RESET}\n"
else
  printf "  ${DIM}Re-run complete. Existing vault and config preserved.${RESET}\n"
fi
echo ""
