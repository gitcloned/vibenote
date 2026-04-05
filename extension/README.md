# Vibenote Chrome Extension

A tiny side panel for capturing pages, quotes, and thoughts into your local Vibenote vault. Local-only, no cloud, no telemetry.

## What it does

Click the Vibenote icon in the toolbar → a side panel slides in showing:

- The current page's title and URL
- An optional thread picker (leave blank to auto-classify)
- A textarea for your comment — paste anything from the page as you read

Hit **Save** (or `⌘↵` / `Ctrl+↵`). One new journal entry is appended to the selected (or auto-classified) thread in `~/.vibenote/threads/<slug>.md`.

The panel stays open while you read, so you can copy-paste from the page without the UI closing.

## Architecture

```
Chrome extension (side panel)
    ↓  native messaging (JSON over stdio)
~/.vibenote/bin/vibenote-bridge.py
    ↓  direct file write
~/.vibenote/threads/<slug>.md
```

- **No daemon.** The bridge is invoked per-message by Chrome and exits.
- **No network.** No telemetry, no cloud sync, no Vibenote-owned server.
- **Local permissions only.** `activeTab` (current tab title/URL on user action), `nativeMessaging` (talk to bridge), `sidePanel`, `storage` (draft autosave).

## Dev install

Requires Vibenote's CLI infrastructure to be installed first, since the extension talks to the native host registered by `install.sh`.

### 1. Install Vibenote

From the repo root:

```bash
./install.sh
```

This installs the Claude Code plugin, the native messaging bridge at `~/.vibenote/bin/vibenote-bridge.py`, and registers the native host manifest with Chrome (macOS path).

### 2. Load the extension (unpacked)

1. Open `chrome://extensions`
2. Toggle **Developer mode** on (top right)
3. Click **Load unpacked**
4. Select this `extension/` folder
5. Copy the **extension ID** shown under the Vibenote tile (32-character string)

### 3. Link the extension to the bridge

Chrome generates a random extension ID for dev-loaded extensions. The native host manifest needs that specific ID in its `allowed_origins` list. Run:

```bash
bash ~/.vibenote/scripts/vn-link-extension.sh <paste-extension-id-here>
```

### 4. Reload the extension

In `chrome://extensions`, click the reload button on the Vibenote tile (or toggle it off/on). Then pin the Vibenote icon to the toolbar for easy access.

### 5. Try it

Navigate to any page and click the Vibenote icon. The side panel should open and show "connected". Type a quick note, hit save, then check `~/.vibenote/threads/` — a new entry should appear.

## Troubleshooting

**Status says "not connected"**

The native messaging bridge can't be reached. Common causes:

- `install.sh` hasn't been run yet
- The extension ID in the native host manifest doesn't match the loaded extension — re-run `vn-link-extension.sh <id>` and reload the extension
- Chrome needs a restart after manifest changes

Check the bridge manifest directly:

```bash
cat "$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.vibenote.bridge.json"
```

The `allowed_origins` should contain your extension's ID, not `__EXTENSION_ID_PLACEHOLDER__`.

**Status says "bridge error"**

The bridge script was found but exited with an error. Open the extension's service worker console (click "Inspect views: service worker" on the extension tile in `chrome://extensions`) and look for error messages.

You can also test the bridge directly from the command line:

```bash
python3 -c "
import struct, json, subprocess
msg = json.dumps({'op': 'ping'}).encode()
result = subprocess.run(
    ['$HOME/.vibenote/bin/vibenote-bridge.py'],
    input=struct.pack('<I', len(msg)) + msg,
    capture_output=True,
)
print('stderr:', result.stderr.decode())
print('stdout:', result.stdout)
"
```

A successful ping returns `{"ok": true, "vault": "/Users/.../.vibenote"}`.

**Saves aren't appearing in the right thread**

Auto-classification uses simple keyword matching against thread slugs and summaries. If it picks the wrong thread, manually select the correct one from the dropdown before saving.

## Files

- `manifest.json` — Manifest V3, permissions, side panel config
- `background.js` — service worker (opens side panel on icon click)
- `sidepanel.html` — UI shell
- `sidepanel.css` — styling (respects system light/dark mode)
- `sidepanel.js` — UI logic + native messaging client + draft autosave

## Status

V1 / MVP — only what's needed to capture: one textarea, title, URL, thread picker. No block composer, no Readability page clipping, no selection-to-quote, no popup Q&A. Those are V2+ candidates if the core flow proves useful.

See `docs/chrome-extension-plan.md` in the repo root for the full build plan and design notes.
