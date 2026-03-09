"""
Context window gauge for Claude Code sessions.

Reads the current session's JSONL transcript and reports context window
utilization: current size, remaining capacity, burn rate, and estimated
turns until compression.

No database required — reads JSONL files directly.
Uses session resolver for accurate multi-session disambiguation.

CLI usage:
    python3 gauge.py                    # auto-detect current session
    python3 gauge.py --all              # all active sessions
    python3 gauge.py --json             # machine-parseable output
    python3 gauge.py --file <path>      # explicit JSONL path
    python3 gauge.py --threshold 150000 # custom compression threshold
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session import resolve_session, resolve_all_sessions

# Empirical compression threshold from analysis of 1,502 transcripts.
# Median peak before compression: 165K. Hard ceiling: 170K.
DEFAULT_THRESHOLD = 165_000


def extract_usage(jsonl_path):
    """
    Parse JSONL and extract per-turn usage data from assistant messages.

    Returns list of dicts with: total_input, output, timestamp.
    Each entry represents one assistant API call with usage data.
    """
    usage_data = []

    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get("type") != "assistant":
                continue

            msg = entry.get("message", {})
            usage = msg.get("usage", {})
            if not usage:
                continue

            input_tokens = usage.get("input_tokens", 0) or 0
            cache_read = usage.get("cache_read_input_tokens", 0) or 0
            cache_creation = usage.get("cache_creation_input_tokens", 0) or 0
            total_input = input_tokens + cache_read + cache_creation

            if total_input == 0:
                continue

            usage_data.append({
                "total_input": total_input,
                "output": usage.get("output_tokens", 0) or 0,
                "timestamp": entry.get("timestamp"),
            })

    return usage_data


def compute_metrics(usage_data, threshold=DEFAULT_THRESHOLD, window=10):
    """
    Compute context gauge metrics from usage data.

    Args:
        usage_data: list of dicts from extract_usage()
        threshold: compression threshold in tokens
        window: number of recent turns for burn rate calculation
    """
    if not usage_data:
        return None

    current = usage_data[-1]["total_input"]
    remaining = max(0, threshold - current)
    pct_used = current / threshold * 100

    # Burn rate: average growth per turn over recent window
    burn_rate = 0
    if len(usage_data) >= 2:
        recent = usage_data[-window:]
        if len(recent) >= 2:
            delta = recent[-1]["total_input"] - recent[0]["total_input"]
            burn_rate = delta / (len(recent) - 1)

    # Estimated turns remaining
    est_turns = None
    if burn_rate > 0:
        est_turns = int(remaining / burn_rate)

    # Detect compression events (large drops in total_input)
    compression_detected = False
    for i in range(1, len(usage_data)):
        if usage_data[i]["total_input"] < usage_data[i - 1]["total_input"] - 1000:
            compression_detected = True
            break

    # Extract session ID from path (filename without extension)
    return {
        "current_size": current,
        "threshold": threshold,
        "remaining": remaining,
        "pct_used": round(pct_used, 1),
        "burn_rate": round(burn_rate),
        "est_turns_remaining": est_turns,
        "total_turns": len(usage_data),
        "compression_detected": compression_detected,
    }


def _fmt_tokens(n):
    """Format token count with comma separators."""
    if n is None:
        return "—"
    return f"{n:,}"


def main():
    parser = argparse.ArgumentParser(
        prog="context-gauge",
        description="Report context window utilization for the current Claude session.",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Show context gauge for all active sessions (modified in last 24h)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="With --all: max age in hours for active sessions (default: 24)",
    )
    parser.add_argument(
        "--file", "-f",
        help="Explicit path to JSONL transcript (default: auto-detect from CWD)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    parser.add_argument(
        "--threshold", "-t",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Compression threshold in tokens (default: {DEFAULT_THRESHOLD:,})",
    )
    parser.add_argument(
        "--window", "-w",
        type=int,
        default=10,
        help="Number of recent turns for burn rate calculation (default: 10)",
    )

    args = parser.parse_args()

    # --all mode: show all active sessions
    if args.all:
        sessions = resolve_all_sessions()
        if not sessions:
            print("No active sessions found.", file=sys.stderr)
            sys.exit(1)

        # Filter by age if --hours specified
        cutoff = time.time() - (args.hours * 3600)

        all_metrics = []
        seen_sessions = set()
        for s in sessions:
            transcript = s.get("transcript_path")
            if not transcript or not os.path.exists(transcript):
                continue
            session_id = s.get("session_id", Path(transcript).stem)
            if session_id in seen_sessions:
                continue
            seen_sessions.add(session_id)
            if os.path.getmtime(transcript) < cutoff:
                continue
            usage_data = extract_usage(transcript)
            if not usage_data:
                continue
            metrics = compute_metrics(usage_data, threshold=args.threshold, window=args.window)
            metrics["session_id"] = session_id
            proj_dir = s.get("project_dir", "")
            metrics["project_slug"] = proj_dir.replace("/", "-") if proj_dir else Path(transcript).parent.name
            metrics["transcript_path"] = transcript
            metrics["claude_pid"] = s.get("claude_pid")
            metrics["pane"] = s.get("pane")
            all_metrics.append(metrics)

        if not all_metrics:
            print("No sessions with usage data found.", file=sys.stderr)
            sys.exit(1)

        if args.json_output:
            print(json.dumps(all_metrics))
        else:
            print(f"{'Project':<40} {'Context':>18} {'%':>6} {'Turns':>6} {'Burn':>8} {'~Left':>6}")
            print("─" * 88)
            for m in all_metrics:
                proj = m["project_slug"]
                # Shorten slug: strip leading dash and common prefix
                if proj.startswith("-Users-kd-"):
                    proj = proj[len("-Users-kd-"):]
                elif proj.startswith("-"):
                    proj = proj[1:]
                proj = proj[:38]
                ctx = f"{_fmt_tokens(m['current_size'])} / {_fmt_tokens(m['threshold'])}"
                pct = f"{m['pct_used']}%"
                turns = str(m["total_turns"])
                burn = f"~{_fmt_tokens(m['burn_rate'])}/t" if m["burn_rate"] > 0 else "—"
                left = f"~{m['est_turns_remaining']}" if m["est_turns_remaining"] is not None else "—"
                flag = " !" if m.get("compression_detected") else ""
                print(f"{proj:<40} {ctx:>18} {pct:>6} {turns:>6} {burn:>8} {left:>6}{flag}")
        sys.exit(0)

    # Find transcript
    if args.file:
        jsonl_path = args.file
        if not os.path.exists(jsonl_path):
            print(f"Error: File not found: {jsonl_path}", file=sys.stderr)
            sys.exit(1)
    else:
        result = resolve_session()
        if result and result.get("transcript_path"):
            jsonl_path = result["transcript_path"]
        else:
            print("Error: No transcript found for current session.", file=sys.stderr)
            print(f"  CWD: {os.getcwd()}", file=sys.stderr)
            print("  Use --file to specify a JSONL path explicitly.", file=sys.stderr)
            sys.exit(1)

    # Extract usage data
    usage_data = extract_usage(jsonl_path)
    if not usage_data:
        if args.json_output:
            print(json.dumps({"error": "no_usage_data", "transcript_path": jsonl_path}))
        else:
            print(f"No usage data in transcript: {jsonl_path}")
        sys.exit(1)

    # Compute metrics
    metrics = compute_metrics(usage_data, threshold=args.threshold, window=args.window)

    # Add path info
    session_id = Path(jsonl_path).stem
    metrics["session_id"] = session_id
    metrics["transcript_path"] = jsonl_path

    if args.json_output:
        print(json.dumps(metrics))
    else:
        print(f"Context: {_fmt_tokens(metrics['current_size'])} / {_fmt_tokens(metrics['threshold'])} tokens ({metrics['pct_used']}%)")
        print(f"Remaining: {_fmt_tokens(metrics['remaining'])} tokens")
        if metrics["burn_rate"] > 0:
            print(f"Burn rate: ~{_fmt_tokens(metrics['burn_rate'])} tokens/turn (last {args.window} turns)")
        else:
            print("Burn rate: — (not enough data or context shrinking)")
        if metrics["est_turns_remaining"] is not None:
            print(f"Est. turns remaining: ~{metrics['est_turns_remaining']}")
        else:
            print("Est. turns remaining: — (insufficient data)")
        print(f"Session: {session_id}")
        print(f"Turns: {metrics['total_turns']}")
        if metrics["compression_detected"]:
            print("Note: Compression event detected in this session")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
