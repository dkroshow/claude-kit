#!/usr/bin/env python3
"""
Ingest a single Claude Code transcript into PostgreSQL.

Usage:
    python3 ingest.py <transcript_path>
    python3 ingest.py --stdin  (reads hook JSON from stdin)
"""

import sys
import json
from pathlib import Path

# Add parent dir to path so clogs package is importable
sys.path.insert(0, str(Path(__file__).parent))

from clogs.parser import parse_transcript
from clogs.db import ingest_transcript


def main():
    if len(sys.argv) < 2:
        print("Usage: ingest.py <transcript_path>", file=sys.stderr)
        print("       ingest.py --stdin", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--stdin":
        # Read hook JSON from stdin
        try:
            hook_data = json.load(sys.stdin)
            transcript_path = hook_data.get("transcript_path", "")
            if not transcript_path:
                # Try session_id to construct path
                session_id = hook_data.get("session_id", "")
                cwd = hook_data.get("cwd", "")
                if not transcript_path:
                    print("Error: no transcript_path in hook input", file=sys.stderr)
                    sys.exit(1)
        except json.JSONDecodeError:
            print("Error: invalid JSON on stdin", file=sys.stderr)
            sys.exit(1)
    else:
        transcript_path = sys.argv[1]

    # Expand ~ in path
    transcript_path = str(Path(transcript_path).expanduser())

    if not Path(transcript_path).exists():
        print(f"Error: file not found: {transcript_path}", file=sys.stderr)
        sys.exit(1)

    parsed = parse_transcript(transcript_path)
    if not parsed:
        print(f"Warning: no messages found in {transcript_path}", file=sys.stderr)
        sys.exit(0)

    try:
        counts = ingest_transcript(parsed)
        session_id = parsed["session"]["session_id"]
        print(f"Ingested session {session_id}: "
              f"{counts['messages']} messages, "
              f"{counts['tool_calls']} tool calls, "
              f"{counts['tool_results']} tool results")
    except Exception as e:
        print(f"Error ingesting {transcript_path}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
