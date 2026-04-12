#!/usr/bin/env bash
# vn-update-check — periodic version check for Vibenote.
#
# Output (one line, or nothing):
#   UPGRADE_AVAILABLE <local> <remote>  — newer version exists on GitHub
#   JUST_UPGRADED <old> <new>           — user just upgraded
#   (nothing)                           — up to date or check skipped
#
# Caches results to avoid hitting GitHub on every session start.
# Cache TTL: 60 min when up-to-date, 720 min when upgrade available.
set -euo pipefail

# ─── Paths ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VIBENOTE_HOME="${VIBENOTE_HOME:-$HOME/.vibenote}"
STATE_DIR="$VIBENOTE_HOME/meta"

# VERSION lives in the vault root (copied there by install.sh).
# Fall back to .last-install-version for older installs.
VERSION_FILE="$VIBENOTE_HOME/VERSION"
if [ ! -f "$VERSION_FILE" ] && [ -f "$VIBENOTE_HOME/.last-install-version" ]; then
  VERSION_FILE="$VIBENOTE_HOME/.last-install-version"
fi
CACHE_FILE="$STATE_DIR/last-update-check"
MARKER_FILE="$STATE_DIR/just-upgraded-from"
REMOTE_URL="${VIBENOTE_REMOTE_VERSION_URL:-https://raw.githubusercontent.com/gitcloned/vibenote/main/VERSION}"

# ─── Step 1: Read local version ─────────────────────────────────
LOCAL=""
if [ -f "$VERSION_FILE" ]; then
  LOCAL="$(cat "$VERSION_FILE" 2>/dev/null | tr -d '[:space:]')"
fi
if [ -z "$LOCAL" ]; then
  exit 0  # No VERSION file → skip check
fi

# ─── Step 2: Check "just upgraded" marker ────────────────────────
if [ -f "$MARKER_FILE" ]; then
  OLD="$(cat "$MARKER_FILE" 2>/dev/null | tr -d '[:space:]')"
  rm -f "$MARKER_FILE"
  if [ -n "$OLD" ] && [ "$OLD" != "$LOCAL" ]; then
    echo "JUST_UPGRADED $OLD $LOCAL"
  fi
fi

# ─── Step 3: Check cache freshness ──────────────────────────────
if [ -f "$CACHE_FILE" ]; then
  CACHED="$(cat "$CACHE_FILE" 2>/dev/null || true)"
  case "$CACHED" in
    UP_TO_DATE*)        CACHE_TTL=60 ;;
    UPGRADE_AVAILABLE*) CACHE_TTL=720 ;;
    *)                  CACHE_TTL=0 ;;
  esac

  STALE=$(find "$CACHE_FILE" -mmin +"$CACHE_TTL" 2>/dev/null || true)
  if [ -z "$STALE" ] && [ "$CACHE_TTL" -gt 0 ]; then
    case "$CACHED" in
      UP_TO_DATE*)
        CACHED_VER="$(echo "$CACHED" | awk '{print $2}')"
        if [ "$CACHED_VER" = "$LOCAL" ]; then
          exit 0  # Cache fresh, versions match
        fi
        ;;
      UPGRADE_AVAILABLE*)
        CACHED_OLD="$(echo "$CACHED" | awk '{print $2}')"
        if [ "$CACHED_OLD" = "$LOCAL" ]; then
          echo "$CACHED"
          exit 0  # Cache fresh, show cached upgrade notice
        fi
        ;;
    esac
  fi
fi

# ─── Step 4: Fetch remote version from GitHub ────────────────────
mkdir -p "$STATE_DIR"

REMOTE=""
REMOTE="$(curl -sf --max-time 5 "$REMOTE_URL" 2>/dev/null || true)"
REMOTE="$(echo "$REMOTE" | tr -d '[:space:]')"

# Validate: must look like a version number
if ! echo "$REMOTE" | grep -qE '^[0-9]+\.[0-9.]+$'; then
  echo "UP_TO_DATE $LOCAL" > "$CACHE_FILE"
  exit 0
fi

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "UP_TO_DATE $LOCAL" > "$CACHE_FILE"
  exit 0
fi

# Versions differ — but only upgrade if remote is NEWER (not older).
# Prevents downgrade notices when running from source ahead of release.
NEWER=$(printf '%s\n%s' "$LOCAL" "$REMOTE" | sort -V | tail -1)
if [ "$NEWER" != "$REMOTE" ] || [ "$NEWER" = "$LOCAL" ]; then
  # Local is ahead of or equal to remote — not an upgrade
  echo "UP_TO_DATE $LOCAL" > "$CACHE_FILE"
  exit 0
fi

# Remote is strictly newer — upgrade available
echo "UPGRADE_AVAILABLE $LOCAL $REMOTE" > "$CACHE_FILE"
echo "UPGRADE_AVAILABLE $LOCAL $REMOTE"
