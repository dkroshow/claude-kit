#!/usr/bin/env python3
"""
Backfill all existing Claude Code transcripts into PostgreSQL.

Discovers all JSONL transcript files under ~/.claude/projects/ and ingests
each one. Safe to run multiple times (idempotent via upsert).

Usage:
    python3 backfill.py [--dry-run] [--project <slug>] [--verbose]
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from clogs.parser import parse_transcript
from clogs.db import ingest_transcript


def discover_transcripts(project_filter=None):
    """
    Discover all JSONL transcript files under ~/.claude/projects/.

    Returns list of dicts with path, project_slug, session_id, size_kb.
    Skips agent-* files (subagent transcripts are handled via parent).
    """
    transcript_dir = Path.home() / ".claude" / "projects"
    transcripts = []

    if not transcript_dir.exists():
        return transcripts

    for project_dir in sorted(transcript_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        if project_dir.name.startswith("."):
            continue

        if project_filter and project_dir.name != project_filter:
            continue

        for jsonl_file in sorted(project_dir.glob("*.jsonl")):
            # Skip agent transcripts
            if jsonl_file.name.startswith("agent-"):
                continue

            stat = jsonl_file.stat()
            transcripts.append({
                "path": str(jsonl_file),
                "project_slug": project_dir.name,
                "session_id": jsonl_file.stem,
                "size_kb": stat.st_size // 1024,
            })

    return transcripts


def main():
    parser = argparse.ArgumentParser(description="Backfill Claude transcripts into PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without ingesting")
    parser.add_argument("--project", help="Only process transcripts for this project slug")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-file details")
    args = parser.parse_args()

    transcripts = discover_transcripts(args.project)
    total = len(transcripts)

    if total == 0:
        print("No transcripts found.")
        return

    total_size = sum(t["size_kb"] for t in transcripts)
    projects = len(set(t["project_slug"] for t in transcripts))
    print(f"Found {total} transcripts across {projects} projects ({total_size:,} KB total)")

    if args.dry_run:
        for t in transcripts:
            print(f"  {t['project_slug']}/{t['session_id']} ({t['size_kb']} KB)")
        print(f"\nDry run complete. Would process {total} files.")
        return

    print()

    totals = {"sessions": 0, "messages": 0, "tool_calls": 0, "tool_results": 0}
    errors = []
    start_time = time.time()

    for i, t in enumerate(transcripts, 1):
        try:
            parsed = parse_transcript(t["path"])
            if parsed:
                counts = ingest_transcript(parsed)
                totals["sessions"] += counts["sessions"]
                totals["messages"] += counts["messages"]
                totals["tool_calls"] += counts["tool_calls"]
                totals["tool_results"] += counts["tool_results"]

                if args.verbose:
                    print(f"  [{i}/{total}] {t['project_slug']}/{t['session_id']}: "
                          f"{counts['messages']} msgs, {counts['tool_calls']} tools")
            else:
                if args.verbose:
                    print(f"  [{i}/{total}] {t['project_slug']}/{t['session_id']}: skipped (empty)")
        except Exception as e:
            errors.append({"file": t["path"], "error": str(e)})
            print(f"  [{i}/{total}] ERROR {t['project_slug']}/{t['session_id']}: {e}",
                  file=sys.stderr)

        # Progress every 50 files
        if i % 50 == 0 and not args.verbose:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            print(f"  Progress: {i}/{total} ({rate:.1f} files/sec)")

    elapsed = time.time() - start_time

    print(f"\nBackfill complete in {elapsed:.1f}s:")
    print(f"  Sessions:     {totals['sessions']}")
    print(f"  Messages:     {totals['messages']:,}")
    print(f"  Tool calls:   {totals['tool_calls']:,}")
    print(f"  Tool results: {totals['tool_results']:,}")
    if errors:
        print(f"  Errors:       {len(errors)}")
        for e in errors:
            print(f"    - {e['file']}: {e['error']}")


if __name__ == "__main__":
    main()
