#!/usr/bin/env bash
set -euo pipefail

# Inputs
ROOT_INPUT=${FOLDER:-}
DAYS=${RETENTION_DAYS:-7}
EXTS=${RETENTION_EXTENSIONS:-"mkv mp4 ts m4v"}
DRY=${DRY_RUN:-true}

# Safety knobs
ALLOW_PREFIX=${ALLOW_PREFIX:-/purge/files}   # only purge under this prefix
SENTINEL_FILE=${SENTINEL_FILE:-.purge-allow}    # must exist at root
SAFETY_MINUTES=${SAFETY_MINUTES:-30}            # skip very recent files
STAY_ON_FS=${STAY_ON_FS:-true}                  # use -xdev

# Resolve absolute root path
if [[ -z "$ROOT_INPUT" ]]; then
  echo "FOLDER env var is required" >&2
  exit 2
fi
ROOT=$(readlink -f -- "$ROOT_INPUT" || true)
if [[ -z "${ROOT:-}" || ! -d "$ROOT" ]]; then
  echo "Resolved ROOT is not a directory: '$ROOT_INPUT' -> '$ROOT'" >&2
  exit 2
fi

# Guard: ensure ROOT under allowed prefix
case "$ROOT" in
  "$ALLOW_PREFIX"|"$ALLOW_PREFIX"/*) ;;  # ok
  *)
    echo "Refusing to purge: ROOT '$ROOT' is outside ALLOW_PREFIX '$ALLOW_PREFIX'" >&2
    exit 2
    ;;
esac

# Guard: require sentinel file
if [[ ! -f "$ROOT/$SENTINEL_FILE" ]]; then
  echo "Refusing to purge: sentinel '$SENTINEL_FILE' not found in '$ROOT'" >&2
  exit 3
fi

# Simple lock to avoid concurrent runs
LOCKDIR="$ROOT/.purger.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "Another purge appears to be running (lock: $LOCKDIR)" >&2
  exit 4
fi
cleanup() { rmdir "$LOCKDIR" 2>/dev/null || true; }
trap cleanup EXIT

# Build extension filters (case-insensitive)
filters=()
for e in $EXTS; do
  filters+=(-o -iname "*.${e}")
done
# Strip leading -o if present
if [[ ${#filters[@]} -gt 0 ]]; then
  filters=("${filters[@]:1}")
fi

echo "Searching $ROOT for files older than $DAYS days, not modified in last ${SAFETY_MINUTES}m, matching: $EXTS"
echo "Safety: ALLOW_PREFIX=$ALLOW_PREFIX, SENTINEL_FILE=$SENTINEL_FILE, STAY_ON_FS=$STAY_ON_FS"

# Common find base
base=(find "$ROOT")
if [[ "$STAY_ON_FS" == "true" ]]; then
  base+=(-xdev)
fi
base+=(-type f -mtime +"$DAYS" -mmin +"$SAFETY_MINUTES")
if [[ ${#filters[@]} -gt 0 ]]; then
  base+=( \( "${filters[@]}" \) )
fi

if [[ "$DRY" == "true" ]]; then
  echo "[DRY-RUN] Files that would be deleted:"
  "${base[@]}" -print
  exit 0
fi

# Execute delete with summary
set +e
COUNT=$("${base[@]}" -print -delete | wc -l)
STATUS=$?
set -e
if [[ $STATUS -ne 0 ]]; then
  echo "Delete run encountered errors (status=$STATUS). Partial deletions may have occurred." >&2
  exit $STATUS
fi

echo "Deleted $COUNT files."