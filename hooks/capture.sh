#!/bin/bash
# Capture a conversation transcript for later review
#
# Usage:
#   ./capture.sh <transcript_path> [source]
#   echo '{"transcript_path":...}' | ./capture.sh --stdin
#
# source: "auto" (from PreCompact) or "manual" (from /capture)

set -e

CAPTURES_DIR=".project/captures"
mkdir -p "$CAPTURES_DIR"

# Parse arguments
if [ "$1" == "--stdin" ]; then
    # Called from PreCompact hook - read JSON from stdin
    HOOK_INPUT=$(cat)
    TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')
    SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id')
    TRIGGER=$(echo "$HOOK_INPUT" | jq -r '.trigger')

    # Only capture on auto-compaction
    if [ "$TRIGGER" != "auto" ]; then
        exit 0
    fi

    SOURCE="auto"
else
    # Called directly with path argument
    TRANSCRIPT_PATH="$1"
    SOURCE="${2:-manual}"
    SESSION_ID=$(basename "$TRANSCRIPT_PATH" .jsonl)
fi

# Expand ~ in path
TRANSCRIPT_PATH="${TRANSCRIPT_PATH/#\~/$HOME}"

# Check transcript exists
if [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo "Error: transcript not found at $TRANSCRIPT_PATH" >&2
    exit 1
fi

# Extract first user message from transcript
FIRST_MESSAGE=$(cat "$TRANSCRIPT_PATH" | jq -r 'select(.type == "user") | .message.content' | head -1 | cut -c1-500)

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create capture file
CAPTURE_FILE="$CAPTURES_DIR/${TIMESTAMP}-capture.md"

cat > "$CAPTURE_FILE" << EOF
# Capture

**Status:** pending
**Timestamp:** $(date -Iseconds)
**Session ID:** $SESSION_ID
**Source:** $SOURCE

## Transcript

\`\`\`
$TRANSCRIPT_PATH
\`\`\`

## First Message

> ${FIRST_MESSAGE}
EOF

echo "$CAPTURE_FILE"
