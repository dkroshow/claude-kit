"""
Conversation understanding CLI for Claude Code sessions.

Extracts structured conversation state — phase, health, context pressure,
activity, and intent — from JSONL transcripts. Designed for consumption
by the james meta-agent via subprocess.

CLI usage:
    python3 understand.py --file <path.jsonl>         # explicit JSONL file
    python3 understand.py --all --json                 # all active sessions
    python3 understand.py <session-id> --json          # by session ID
    python3 understand.py <session-id>                 # human-readable
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session import resolve_session, resolve_all_sessions
from gauge import compute_metrics, DEFAULT_THRESHOLD
from parser import parse_transcript
from conversation_state import detect_phase, assess_health, summarize_activity, extract_intent


def _usage_from_messages(messages: list) -> list:
    """
    Derive gauge-compatible usage data from parsed messages.

    Avoids re-reading the JSONL file — parse_transcript() already extracts
    the token fields that extract_usage() would read from disk.
    """
    usage_data = []
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        input_tokens = msg.get("input_tokens") or 0
        cache_read = msg.get("cache_read_input_tokens") or 0
        cache_creation = msg.get("cache_creation_input_tokens") or 0
        total_input = input_tokens + cache_read + cache_creation
        if total_input == 0:
            continue
        usage_data.append({
            "total_input": total_input,
            "output": msg.get("output_tokens") or 0,
            "timestamp": msg.get("timestamp"),
        })
    return usage_data


def analyze_session(jsonl_path: str, live: bool = False) -> dict:
    """
    Analyze a single session from its JSONL transcript.

    Returns structured state dict or None if transcript is empty/invalid.
    """
    parsed = parse_transcript(jsonl_path)
    if not parsed or not parsed["messages"]:
        return None

    session = parsed["session"]
    messages = parsed["messages"]
    tool_results = parsed["tool_results"]

    # Context pressure — derived from already-parsed messages (no second file read)
    usage_data = _usage_from_messages(messages)
    context = compute_metrics(usage_data) if usage_data else {
        "current_size": 0,
        "threshold": DEFAULT_THRESHOLD,
        "remaining": DEFAULT_THRESHOLD,
        "pct_used": 0.0,
        "burn_rate": 0,
        "est_turns_remaining": None,
        "total_turns": 0,
        "compression_detected": False,
    }
    # Add compression data from parser
    context["compression_count"] = session.get("compression_count", 0)

    # Conversation state
    phase = detect_phase(messages, live=live)
    health = assess_health(messages, tool_results)
    activity = summarize_activity(messages)
    intent = extract_intent(messages)

    return {
        "session_id": session.get("session_id"),
        "project_slug": session.get("project_slug"),
        "transcript_path": jsonl_path,
        "phase": phase,
        "health": health,
        "context": context,
        "activity": activity,
        "intent": intent,
    }


def _fmt_tokens(n):
    if n is None:
        return "—"
    return f"{n:,}"


def print_human(state: dict):
    """Print human-readable session state."""
    sid = state["session_id"] or "unknown"
    proj = state.get("project_slug") or "—"
    phase = state["phase"]
    health = state["health"]
    ctx = state["context"]
    activity = state["activity"]
    intent = state["intent"]

    print(f"Session: {sid}")
    print(f"Project: {proj}")
    print(f"Phase:   {phase['current']} ({phase['confidence']} confidence)")

    # Health
    if health["stuck"]:
        print(f"Health:  STUCK (error rate {health['error_rate']:.0%}, {health['retry_loops']} retry loops)")
    else:
        idle_str = f", active {health['idle_seconds']}s ago" if health["idle_seconds"] is not None else ""
        print(f"Health:  OK (error rate {health['error_rate']:.0%}{idle_str})")

    # Context
    pct = ctx["pct_used"]
    remaining = _fmt_tokens(ctx["remaining"])
    burn = f", burn ~{_fmt_tokens(ctx['burn_rate'])}/turn" if ctx.get("burn_rate", 0) > 0 else ""
    est = f", ~{ctx['est_turns_remaining']} turns left" if ctx.get("est_turns_remaining") else ""
    compress = f", {ctx['compression_count']} compressions" if ctx.get("compression_count") else ""
    print(f"Context: {_fmt_tokens(ctx['current_size'])} / {_fmt_tokens(ctx['threshold'])} ({pct}%){burn}{est}{compress}")

    # Activity
    fr = len(activity["files_read"])
    fe = len(activity["files_edited"])
    cmds = len(activity["commands_run"])
    agents = activity["agents_spawned"]
    print(f"Activity: {fr} files read, {fe} edited, {cmds} commands, {agents} agents spawned")

    # Intent
    if intent["initial_prompt"]:
        initial = intent["initial_prompt"].replace("\n", " ")[:80]
        print(f"Intent:  \"{initial}...\" ({intent['turn_count']} turns)")


def main():
    parser = argparse.ArgumentParser(
        prog="understand",
        description="Extract structured conversation state from Claude Code sessions.",
    )
    parser.add_argument(
        "session_id",
        nargs="?",
        help="Claude session UUID (resolves via session resolver)",
    )
    parser.add_argument(
        "--file", "-f",
        help="Explicit path to JSONL transcript",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Analyze all active sessions (modified in last 24h)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="With --all: max age in hours for active sessions (default: 24)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )

    args = parser.parse_args()

    # --all mode
    if args.all:
        sessions = resolve_all_sessions()
        if not sessions:
            print("No active sessions found.", file=sys.stderr)
            sys.exit(1)

        cutoff = time.time() - (args.hours * 3600)
        results = []
        seen = set()

        for s in sessions:
            transcript = s.get("transcript_path")
            if not transcript or not os.path.exists(transcript):
                continue
            session_id = s.get("session_id", Path(transcript).stem)
            if session_id in seen:
                continue
            seen.add(session_id)
            if os.path.getmtime(transcript) < cutoff:
                continue

            state = analyze_session(transcript, live=True)
            if state:
                results.append(state)

        if not results:
            print("No sessions with data found.", file=sys.stderr)
            sys.exit(1)

        if args.json_output:
            print(json.dumps(results))
        else:
            for i, state in enumerate(results):
                if i > 0:
                    print(f"\n{'─' * 60}\n")
                print_human(state)
        sys.exit(0)

    # Single session mode
    jsonl_path = None

    if args.file:
        jsonl_path = args.file
        if not os.path.exists(jsonl_path):
            print(f"Error: File not found: {jsonl_path}", file=sys.stderr)
            sys.exit(1)
    elif args.session_id:
        # Try to find transcript by session ID
        # First check if it's a file path
        if os.path.exists(args.session_id):
            jsonl_path = args.session_id
        else:
            # Look up in standard locations
            projects_root = Path.home() / ".claude/projects"
            if projects_root.is_dir():
                for projects_dir in projects_root.iterdir():
                    if not projects_dir.is_dir():
                        continue
                    candidate = projects_dir / f"{args.session_id}.jsonl"
                    if candidate.exists():
                        jsonl_path = str(candidate)
                        break
            if not jsonl_path:
                print(f"Error: No transcript found for session: {args.session_id}", file=sys.stderr)
                sys.exit(1)
    else:
        # Auto-detect current session
        result = resolve_session()
        if result and result.get("transcript_path"):
            jsonl_path = result["transcript_path"]
        else:
            print("Error: No transcript found. Use --file or provide a session ID.", file=sys.stderr)
            sys.exit(1)

    live = not args.file  # live=True when auto-detected or by session ID
    state = analyze_session(jsonl_path, live=live)
    if not state:
        print(f"Error: No data in transcript: {jsonl_path}", file=sys.stderr)
        sys.exit(1)

    if args.json_output:
        print(json.dumps(state))
    else:
        print_human(state)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
