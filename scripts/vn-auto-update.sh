#!/usr/bin/env bash
# vn-auto-update.sh — background auto-updater for Vibenote.
#
# Downloads the latest tarball from GitHub, re-runs install.sh, and writes
# a marker so the next session shows "updated from X to Y."
#
# Designed to run in the background (nohup ... &) from session-start.sh.
# Fails silently — never breaks the current session.
set -euo pipefail

VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"
STATE_DIR="$VIBENOTE_HOME/meta"
REPO_URL="https://github.com/gitcloned/vibenote"
BRANCH="${VIBENOTE_BRANCH:-main}"
TARBALL_URL="${VIBENOTE_TARBALL_URL:-${REPO_URL}/archive/refs/heads/${BRANCH}.tar.gz}"
LOCK_FILE="$STATE_DIR/update.lock"

# ─── Prevent concurrent updates ─────────────────────────────────
if [ -f "$LOCK_FILE" ]; then
  # Check if lock is stale (older than 10 minutes)
  STALE=$(find "$LOCK_FILE" -mmin +10 2>/dev/null || true)
  if [ -z "$STALE" ]; then
    exit 0  # Another update is running
  fi
  rm -f "$LOCK_FILE"
fi

mkdir -p "$STATE_DIR"
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# ─── Read current local version ──────────────────────────────────
LOCAL_VERSION=""
if [ -f "$VIBENOTE_HOME/VERSION" ]; then
  LOCAL_VERSION="$(cat "$VIBENOTE_HOME/VERSION" | tr -d '[:space:]')"
fi
if [ -z "$LOCAL_VERSION" ]; then
  exit 0  # No version info — can't update safely
fi

# ─── Download the tarball ────────────────────────────────────────
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"; rm -f "$LOCK_FILE"' EXIT

if ! curl -fsSL --max-time 30 "$TARBALL_URL" | tar xz -C "$TMPDIR" 2>/dev/null; then
  exit 0  # Download failed — try again next session
fi

# Find the extracted directory
EXTRACTED="$(find "$TMPDIR" -maxdepth 1 -type d -name 'vibenote-*' | head -1)"
if [ -z "$EXTRACTED" ] || [ ! -f "$EXTRACTED/VERSION" ]; then
  exit 0  # Bad download
fi

# ─── Check remote version ────────────────────────────────────────
REMOTE_VERSION="$(cat "$EXTRACTED/VERSION" | tr -d '[:space:]')"
if [ "$LOCAL_VERSION" = "$REMOTE_VERSION" ]; then
  exit 0  # Already up to date (race with cache)
fi

# ─── Run install.sh from the downloaded code ─────────────────────
# Write the "upgrading from" marker BEFORE install (in case install updates VERSION)
echo "$LOCAL_VERSION" > "$STATE_DIR/just-upgraded-from"

if bash "$EXTRACTED/install.sh" --quiet >/dev/null 2>&1; then
  # Success — cache will be refreshed next session
  echo "UP_TO_DATE $REMOTE_VERSION" > "$STATE_DIR/last-update-check"
else
  # Install failed — remove marker so we don't show false "upgraded" message
  rm -f "$STATE_DIR/just-upgraded-from"
fi
