#!/usr/bin/env bash
# Links a dev-loaded Chrome extension to the Vibenote native messaging host.
#
# Usage: vn-link-extension.sh <extension-id>
#
# After dev-loading the extension in chrome://extensions, copy the generated
# extension ID (32-character lowercase string) and pass it to this script.
# It rewrites the native host manifest to allow that specific extension to
# invoke the bridge.
#
# When we ship to the Chrome Web Store, the extension ID is stable and known
# in advance, so install.sh sets it directly and this script becomes unused.

set -e

EXT_ID="$1"
if [ -z "$EXT_ID" ]; then
  echo "Usage: $0 <extension-id>" >&2
  echo "" >&2
  echo "Find the extension ID in chrome://extensions after loading unpacked." >&2
  exit 1
fi

# Basic validation: extension IDs are 32 lowercase letters.
if ! echo "$EXT_ID" | grep -qE '^[a-p]{32}$'; then
  echo "Warning: '$EXT_ID' doesn't look like a valid Chrome extension ID" >&2
  echo "(Expected: 32 lowercase letters a-p)" >&2
  echo "Proceeding anyway..." >&2
fi

MANIFEST="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.vibenote.bridge.json"

if [ ! -f "$MANIFEST" ]; then
  echo "Error: native host manifest not found at:" >&2
  echo "  $MANIFEST" >&2
  echo "" >&2
  echo "Run install.sh first to register the bridge." >&2
  exit 1
fi

# Replace the allowed_origins line with the given extension ID.
# Use Python for portable JSON editing (works on macOS without sed quirks).
python3 - <<PYEOF
import json, sys
from pathlib import Path

manifest_path = Path("$MANIFEST")
data = json.loads(manifest_path.read_text())
data["allowed_origins"] = [f"chrome-extension://$EXT_ID/"]
manifest_path.write_text(json.dumps(data, indent=2) + "\n")
print(f"  Linked extension {'$EXT_ID'[:12]}... to Vibenote bridge")
PYEOF

echo ""
echo "Done. Close and reopen the Vibenote extension in Chrome to pick up the change."
