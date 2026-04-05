#!/usr/bin/env bash
# Deploys current SKILL.md into ~/.claude/CLAUDE.md
# Run this after any change to skills/vibenote/SKILL.md
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
PLUGIN_ROOT="$CLAUDE_DIR/plugins/cache/local/vibenote/1.0.0"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
SKILL_MD="$SCRIPT_DIR/skills/vibenote/SKILL.md"

# Guard: CLAUDE.md must have the VIBENOTE block (install.sh must have run first)
if ! grep -q "VIBENOTE START" "$CLAUDE_MD" 2>/dev/null; then
  echo "Error: VIBENOTE block not found in $CLAUDE_MD"
  echo "Run install.sh first."
  exit 1
fi

# Copy updated skill + scripts to plugin dir
cp -r "$SCRIPT_DIR/skills" "$PLUGIN_ROOT/"
cp -r "$SCRIPT_DIR/scripts" "$PLUGIN_ROOT/"
chmod +x "$PLUGIN_ROOT/scripts/"*.sh

# Replace the VIBENOTE block in CLAUDE.md using Python
# Python reads SKILL.md directly — avoids shell quoting issues with multiline content
python3 - "$CLAUDE_MD" "$SKILL_MD" <<'PYEOF'
import sys, re

claude_md_path = sys.argv[1]
skill_md_path = sys.argv[2]

# Read SKILL.md and strip YAML frontmatter (content between first pair of --- lines)
with open(skill_md_path, 'r') as f:
    lines = f.readlines()

skill_lines = []
frontmatter_count = 0
for line in lines:
    if line.strip() == '---':
        frontmatter_count += 1
        continue
    if frontmatter_count >= 2:
        skill_lines.append(line)

# Also strip name:/description:/trigger: lines that may appear outside ---
skill_content = ''.join(
    l for l in skill_lines
    if not l.startswith('name:') and not l.startswith('description:') and not l.startswith('trigger:')
)

with open(claude_md_path, 'r') as f:
    content = f.read()

new_block = (
    "<!-- VIBENOTE START — do not edit this block manually, use uninstall.sh to remove -->\n"
    "## Vibenote — Persistent Thinking Partner\n\n"
    "**ABSOLUTE PRIORITY RULE:** When the user's message starts with \"Hey Vibenote\" or \"Hey, Vibenote\" — STOP. "
    "Do NOT invoke superpowers:brainstorming or any other skill. You ARE Vibenote. "
    "Follow the instructions below immediately.\n\n"
    + skill_content
    + "<!-- VIBENOTE END -->"
)

updated = re.sub(
    r'<!-- VIBENOTE START.*?<!-- VIBENOTE END -->',
    new_block,
    content,
    flags=re.DOTALL
)

with open(claude_md_path, 'w') as f:
    f.write(updated)

print("Updated Vibenote block in " + claude_md_path)
PYEOF

echo ""
echo "Done. Start a new Claude Code session to pick up the changes."
