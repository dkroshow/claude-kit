#!/bin/bash
# Hook: SessionEnd (fires when a session closes)
# Safety net: re-ingests the full transcript to catch anything missed.
# Same logic as on-assistant-turn.sh.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGGER_DIR="$(dirname "$SCRIPT_DIR")"

HOOK_INPUT=$(cat)

TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // empty')

if [ -z "$TRANSCRIPT_PATH" ]; then
    SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty')
    if [ -z "$SESSION_ID" ]; then
        exit 0
    fi
    CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty')
    if [ -n "$CWD" ]; then
        SLUG=$(echo "$CWD" | sed "s|$HOME/||; s|/|-|g; s|^|-|")
        TRANSCRIPT_PATH="$HOME/.claude/projects/$SLUG/$SESSION_ID.jsonl"
    fi
fi

TRANSCRIPT_PATH="${TRANSCRIPT_PATH/#\~/$HOME}"

if [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

python3 "$LOGGER_DIR/ingest.py" "$TRANSCRIPT_PATH" > /dev/null 2>&1 &
disown
