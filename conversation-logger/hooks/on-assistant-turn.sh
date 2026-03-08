#!/bin/bash
# Hook: Stop (fires after each assistant turn)
# Ingests the current transcript into PostgreSQL.
# Reads hook JSON from stdin, extracts transcript_path, calls ingest.py.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGGER_DIR="$(dirname "$SCRIPT_DIR")"

# Read hook JSON from stdin
HOOK_INPUT=$(cat)

# Extract transcript path from hook JSON
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // empty')

if [ -z "$TRANSCRIPT_PATH" ]; then
    # Fallback: try to find it from session_id
    SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty')
    if [ -z "$SESSION_ID" ]; then
        exit 0  # No transcript info available, skip silently
    fi

    # Search for the transcript file
    CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty')
    if [ -n "$CWD" ]; then
        SLUG=$(echo "$CWD" | sed "s|$HOME/||; s|/|-|g; s|^|-|")
        TRANSCRIPT_PATH="$HOME/.claude/projects/$SLUG/$SESSION_ID.jsonl"
    fi
fi

# Expand ~ in path
TRANSCRIPT_PATH="${TRANSCRIPT_PATH/#\~/$HOME}"

if [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0  # Transcript not found, skip silently
fi

# Run ingestion in background (fork + disown so the hook returns instantly)
python3 "$LOGGER_DIR/ingest.py" "$TRANSCRIPT_PATH" > /dev/null 2>&1 &
disown
