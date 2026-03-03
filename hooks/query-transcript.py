#!/usr/bin/env python3
"""
Simple, flexible transcript query tool.

Like grep/head/tail, but for Claude Code conversation transcripts.
The subagent handles semantic translation -- this tool just filters and returns.

Usage:
    ./query-transcript.py <transcript.jsonl> [options]
    ./query-transcript.py --all [options]          # Search all transcripts
    ./query-transcript.py --index [options]        # Search indexed transcripts

Examples:
    # Search for pattern (case-insensitive)
    ./query-transcript.py transcript.jsonl --grep "error"

    # Search ALL transcripts
    ./query-transcript.py --all --grep "authentication"

    # Filter by role
    ./query-transcript.py transcript.jsonl --role user

    # Get first/last N messages
    ./query-transcript.py transcript.jsonl --head 10
    ./query-transcript.py transcript.jsonl --tail 20

    # Context around matches (like grep -C)
    ./query-transcript.py transcript.jsonl --grep "bug" --context 2

    # List available transcripts
    ./query-transcript.py --list
"""

import json
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


def get_transcript_dir() -> Path:
    """Get the Claude projects transcript directory."""
    return Path.home() / ".claude" / "projects"


def list_transcripts() -> List[Dict]:
    """List all available transcripts with metadata."""
    transcript_dir = get_transcript_dir()
    transcripts = []

    if not transcript_dir.exists():
        return transcripts

    for project_dir in transcript_dir.iterdir():
        if not project_dir.is_dir():
            continue
        for jsonl_file in project_dir.glob("*.jsonl"):
            # Skip agent transcripts
            if jsonl_file.name.startswith("agent-"):
                continue

            stat = jsonl_file.stat()
            # Get first user message as preview
            preview = ""
            try:
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        entry = json.loads(line)
                        if entry.get("type") == "user":
                            content = entry.get("message", {})
                            if isinstance(content, dict):
                                preview = str(content.get("content", ""))[:100]
                            else:
                                preview = str(content)[:100]
                            break
            except Exception:
                pass

            transcripts.append({
                "path": str(jsonl_file),
                "project": project_dir.name,
                "session": jsonl_file.stem,
                "size_kb": stat.st_size // 1024,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "preview": preview
            })

    return sorted(transcripts, key=lambda x: x["modified"], reverse=True)


def extract_content(entry: dict) -> str:
    """Extract text content from a transcript entry."""
    entry_type = entry.get("type")

    if entry_type == "user":
        content = entry.get("message", {})
        if isinstance(content, dict):
            raw = content.get("content", "")
        else:
            raw = content
    elif entry_type == "assistant":
        msg = entry.get("message", {})
        raw = msg.get("content", [])
    else:
        return ""

    # Flatten content
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        parts = []
        for item in raw:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif item.get("type") == "tool_use":
                    parts.append(f"[Tool: {item.get('name', 'unknown')}]")
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(raw) if raw else ""


def parse_transcript(filepath: str) -> List[Dict]:
    """Parse transcript into list of messages."""
    messages = []
    idx = 0

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type")
                if entry_type not in ("user", "assistant"):
                    continue

                content = extract_content(entry)
                if not content.strip():
                    continue

                messages.append({
                    "index": idx,
                    "role": entry_type,
                    "content": content.strip(),
                    "source": filepath
                })
                idx += 1
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)

    return messages


def format_message(msg: dict, verbose: bool = False, show_source: bool = False) -> str:
    """Format a message for output."""
    idx = msg["index"]
    content = msg["content"]
    source = msg.get("source", "")

    prefix = ""
    if show_source:
        source_name = Path(source).stem[:12] if source else "?"
        prefix = f"[{source_name}] "

    if verbose:
        header = f"{prefix}[{idx}] {msg['role'].upper()}:"
        if show_source and source:
            header += f"\n  Source: {source}"
        return f"{header}\n{content}\n"
    else:
        display = content
        if len(display) > 500:
            display = display[:500] + "... [truncated]"
        return f"{prefix}[{idx}] {msg['role'].upper()}: {display}"


def apply_filters(messages: List[Dict], args) -> List[Dict]:
    """Apply filters to messages."""
    # Role filter
    if args.role:
        messages = [m for m in messages if m["role"] == args.role]

    # Range filters
    if args.after is not None:
        messages = [m for m in messages if m["index"] > args.after]
    if args.before is not None:
        messages = [m for m in messages if m["index"] < args.before]

    # Grep filter (with context)
    if args.grep:
        pattern = re.compile(args.grep, re.IGNORECASE)
        if args.context > 0:
            all_messages = messages
            match_indices = set()
            for i, m in enumerate(all_messages):
                if pattern.search(m["content"]):
                    for j in range(max(0, i - args.context), min(len(all_messages), i + args.context + 1)):
                        match_indices.add(j)
            messages = [all_messages[i] for i in sorted(match_indices)]
        else:
            messages = [m for m in messages if pattern.search(m["content"])]

    # Head/tail
    if args.head:
        messages = messages[:args.head]
    if args.tail:
        messages = messages[-args.tail:]

    return messages


def main():
    parser = argparse.ArgumentParser(
        description="Query Claude Code transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("transcript", nargs="?", help="Path to transcript JSONL")
    parser.add_argument("--all", "-a", action="store_true", help="Search all transcripts")
    parser.add_argument("--list", action="store_true", help="List available transcripts")
    parser.add_argument("--grep", "-g", help="Search pattern (regex, case-insensitive)")
    parser.add_argument("--role", "-r", choices=["user", "assistant"], help="Filter by role")
    parser.add_argument("--head", type=int, help="First N messages")
    parser.add_argument("--tail", type=int, help="Last N messages")
    parser.add_argument("--after", type=int, help="Messages after index N")
    parser.add_argument("--before", type=int, help="Messages before index N")
    parser.add_argument("--context", "-C", type=int, default=0, help="Context lines around grep matches")
    parser.add_argument("--verbose", "-v", action="store_true", help="Full message content")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--count", action="store_true", help="Just count matches")
    parser.add_argument("--limit", "-l", type=int, default=50, help="Max results per transcript (default: 50)")

    args = parser.parse_args()

    # List mode
    if args.list:
        transcripts = list_transcripts()

        if args.json:
            print(json.dumps(transcripts, indent=2))
        else:
            for t in transcripts[:20]:
                print(f"  {t['modified']} | {t['size_kb']:>6}KB | {t['path']}")
                if t['preview']:
                    print(f"    > {t['preview'][:80]}...")
        return

    # Determine which transcripts to search
    transcript_paths = []

    if args.all:
        transcripts = list_transcripts()
        transcript_paths = [t['path'] for t in transcripts]
    elif args.transcript:
        filepath = Path(args.transcript).expanduser()
        if not filepath.exists():
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        transcript_paths = [str(filepath)]
    else:
        parser.error("transcript path required (or use --all, --list)")

    # Collect all messages
    all_messages = []
    show_source = len(transcript_paths) > 1

    for path in transcript_paths:
        messages = parse_transcript(path)
        messages = apply_filters(messages, args)

        if show_source and args.limit:
            messages = messages[:args.limit]

        all_messages.extend(messages)

    # Apply global tail/head after collecting (for multi-transcript)
    if show_source:
        if args.tail:
            all_messages = all_messages[-args.tail:]
        if args.head:
            all_messages = all_messages[:args.head]

    # Output
    if args.count:
        print(len(all_messages))
    elif args.json:
        print(json.dumps(all_messages, indent=2))
    else:
        if not all_messages:
            print("No matches found.")
        for msg in all_messages:
            print(format_message(msg, args.verbose, show_source))
            if args.verbose:
                print("-" * 40)


if __name__ == "__main__":
    main()
