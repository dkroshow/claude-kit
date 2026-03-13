"""
Claude Code session resolver.

Maps an execution context (tmux pane, Claude tool call, explicit PID) to the
correct Claude Code session UUID and JSONL transcript path.

Resolution signals (in priority order):
  1. PPID walk — from inside a tool call, walk up to find the Claude process
  2. Tmux pane → shell PID → Claude child process
  3. Explicit PID
  4. lsof anchor UUID (older Claude versions keep ~/.claude/tasks/<uuid>/ open)
  5. history.jsonl — most recent sessionId for the project
  6. Newest JSONL by mtime (fallback, same as old gauge behavior)

CLI usage:
    python3 session.py                    # auto-detect from inside Claude
    python3 session.py --pane %94         # specific tmux pane
    python3 session.py --pid 68792        # explicit Claude PID
    python3 session.py --all              # all active sessions
    python3 session.py --json             # JSON output
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _run(cmd, timeout=5):
    """Run a subprocess and return stdout, or empty string on failure."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _get_comm(pid):
    """Get the command name for a PID."""
    return _run(["ps", "-o", "comm=", "-p", str(pid)])


def find_claude_pid(pane=None, pid=None):
    """
    Find the Claude Code process PID.

    Resolution order:
      1. Explicit pid (validated as a Claude process)
      2. Tmux pane → shell PID → Claude child
      3. $TMUX_PANE env var → treated as pane
      4. PPID walk from current process
    """
    # 1. Explicit PID
    if pid is not None:
        comm = _get_comm(pid)
        if "claude" in comm.lower():
            return pid
        return None

    # 2. Tmux pane
    if pane is None:
        pane = os.environ.get("TMUX_PANE")

    if pane:
        claude_pid = _claude_pid_from_pane(pane)
        if claude_pid:
            return claude_pid

    # 3. PPID walk
    return _claude_pid_from_ppid_walk()


def _claude_pid_from_pane(pane):
    """Find Claude PID running in a specific tmux pane."""
    # Get shell PID for this pane
    output = _run(["tmux", "list-panes", "-a", "-F", "#{pane_id} #{pane_pid}"])
    if not output:
        return None

    shell_pid = None
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == pane:
            shell_pid = int(parts[1])
            break

    if not shell_pid:
        return None

    # Find Claude child of this shell
    return _find_claude_child(shell_pid)


def _find_claude_child(parent_pid):
    """Find a Claude process that is a child of the given PID."""
    output = _run(["ps", "-eo", "pid,ppid,comm"])
    if not output:
        return None

    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            try:
                child_pid = int(parts[0])
                ppid = int(parts[1])
                comm = parts[2]
            except (ValueError, IndexError):
                continue
            if ppid == parent_pid and "claude" in comm.lower():
                return child_pid
    return None


def _claude_pid_from_ppid_walk():
    """Walk the PPID chain from current process to find a Claude ancestor."""
    pid = os.getpid()
    visited = set()
    while pid > 1 and pid not in visited:
        visited.add(pid)
        comm = _get_comm(pid)
        if "claude" in comm.lower():
            return pid
        # Get parent PID
        ppid_str = _run(["ps", "-o", "ppid=", "-p", str(pid)])
        if not ppid_str:
            break
        try:
            pid = int(ppid_str)
        except ValueError:
            break
    return None


def get_process_context(claude_pid):
    """
    Extract context from a Claude process via lsof and ps.

    Returns dict with: cwd, anchor_uuid, project_slug, tty.
    """
    ctx = {"cwd": None, "anchor_uuid": None, "project_slug": None, "tty": None}

    # CWD from lsof
    lsof_output = _run(["lsof", "-p", str(claude_pid)])
    if lsof_output:
        for line in lsof_output.splitlines():
            if " cwd " in line:
                # Last field is the path
                parts = line.split()
                ctx["cwd"] = parts[-1] if parts else None

            # Anchor UUID from tasks/ directory (older Claude versions)
            if ".claude/tasks/" in line and "DIR" in line:
                match = _UUID_RE.search(line)
                if match:
                    ctx["anchor_uuid"] = match.group()

    # Fallback CWD from /proc or ps
    if not ctx["cwd"]:
        cwd = _run(["pwdx", str(claude_pid)])  # Linux
        if cwd and ":" in cwd:
            ctx["cwd"] = cwd.split(":", 1)[1].strip()

    # TTY
    ctx["tty"] = _run(["ps", "-o", "tty=", "-p", str(claude_pid)]) or None

    # Derive project slug from CWD
    if ctx["cwd"]:
        ctx["project_slug"] = ctx["cwd"].replace("/", "-")

    return ctx


def _get_all_claude_pids():
    """Return list of all running Claude process PIDs."""
    output = _run(["ps", "-eo", "pid,comm"])
    pids = []
    if not output:
        return pids
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            try:
                pid = int(parts[0])
                comm = parts[1]
                if comm.lower() == "claude":
                    pids.append(pid)
            except (ValueError, IndexError):
                continue
    return pids


def _get_sibling_anchors(claude_pid, same_cwd_pids):
    """Get anchor UUIDs from sibling Claude processes (same CWD, different PID)."""
    anchors = set()
    for pid in same_cwd_pids:
        if pid == claude_pid:
            continue
        lsof_output = _run(["lsof", "-p", str(pid)])
        if lsof_output:
            for line in lsof_output.splitlines():
                if ".claude/tasks/" in line and "DIR" in line:
                    match = _UUID_RE.search(line)
                    if match:
                        anchors.add(match.group())
    return anchors


def _session_from_history(project_dir, cwd):
    """
    Find the most recent sessionId for a project from history.jsonl.

    Args:
        project_dir: Path to the ~/.claude/projects/<slug>/ directory (or None)
        cwd: The project's working directory path (e.g., /home/user/my-project)

    Returns (session_id, transcript_path) or (None, None).
    """
    history_path = Path.home() / ".claude" / "history.jsonl"
    if not history_path.exists():
        return None, None

    best_session = None
    best_ts = 0

    try:
        with open(history_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_project = entry.get("project", "")
                session_id = entry.get("sessionId")
                ts = entry.get("timestamp", 0)

                if not session_id or ts <= best_ts:
                    continue

                # Match by exact project path
                if cwd and entry_project == cwd:
                    best_session = session_id
                    best_ts = ts
    except OSError:
        return None, None

    if best_session and project_dir:
        transcript = project_dir / f"{best_session}.jsonl"
        if transcript.exists():
            return best_session, str(transcript)

    return best_session, None


def resolve_session(pid=None, pane=None, project_dir=None):
    """
    Resolve the current Claude session.

    Main entry point. Returns dict with:
      session_id, claude_pid, project_dir, transcript_path,
      anchor_uuid, pane, method

    Returns None if resolution fails entirely.
    """
    # Step 1: Find Claude PID
    claude_pid = find_claude_pid(pane=pane, pid=pid)

    method = "unknown"
    ctx = {"cwd": None, "anchor_uuid": None, "project_slug": None, "tty": None}

    # Step 2: Get process context
    if claude_pid:
        ctx = get_process_context(claude_pid)
        if pane:
            method = "pane"
        elif pid:
            method = "explicit_pid"
        else:
            method = "ppid_walk"

    # Use explicit project_dir if provided
    if project_dir:
        ctx["cwd"] = str(project_dir)
        ctx["project_slug"] = str(project_dir).replace("/", "-")

    # If we still don't have a CWD, use the current working directory
    if not ctx["cwd"]:
        ctx["cwd"] = os.getcwd()
        ctx["project_slug"] = ctx["cwd"].replace("/", "-")

    # Step 3: Find JSONL candidates
    slug = ctx["project_slug"]
    proj_dir = Path.home() / ".claude" / "projects" / slug
    if not proj_dir.is_dir():
        # Try fallback via history.jsonl
        session_id, transcript = _session_from_history(None, ctx["cwd"])
        if session_id:
            return {
                "session_id": session_id,
                "claude_pid": claude_pid,
                "project_dir": ctx["cwd"],
                "transcript_path": transcript,
                "anchor_uuid": ctx.get("anchor_uuid"),
                "pane": pane,
                "method": f"{method}+history",
            }
        return None

    jsonl_files = list(proj_dir.glob("*.jsonl"))
    if not jsonl_files:
        return None

    # Step 4: Single Claude process for this CWD → simple case
    if claude_pid:
        same_cwd_pids = [
            p for p in _get_all_claude_pids()
            if p != claude_pid and _pid_cwd(p) == ctx["cwd"]
        ]
    else:
        same_cwd_pids = []

    if not same_cwd_pids:
        # Only one Claude process (or no PID info) — use newest by mtime
        newest = max(jsonl_files, key=lambda f: f.stat().st_mtime)
        return {
            "session_id": newest.stem,
            "claude_pid": claude_pid,
            "project_dir": ctx["cwd"],
            "transcript_path": str(newest),
            "anchor_uuid": ctx.get("anchor_uuid"),
            "pane": pane,
            "method": f"{method}+mtime",
        }

    # Step 5: Multiple Claude processes in same CWD — disambiguate
    candidates = set(f.stem for f in jsonl_files)

    # 5a: Anchor exclusion — remove sibling anchors from candidates
    sibling_anchors = _get_sibling_anchors(claude_pid, same_cwd_pids)
    if sibling_anchors:
        candidates -= sibling_anchors
        method += "+anchor_exclusion"

    # 5b: If we have our own anchor, prefer files born near process start
    # (anchor matches first session, may not be current after /clear)

    # 5c: Filter to remaining candidate files and rank by mtime
    candidate_files = [f for f in jsonl_files if f.stem in candidates]
    if not candidate_files:
        candidate_files = jsonl_files  # Fallback to all files

    newest = max(candidate_files, key=lambda f: f.stat().st_mtime)

    # Step 6: Validate via history.jsonl
    hist_session, _ = _session_from_history(proj_dir, ctx["cwd"])
    if hist_session and hist_session in candidates:
        # history.jsonl agrees with a candidate — use it if it's recent
        hist_file = proj_dir / f"{hist_session}.jsonl"
        if hist_file.exists():
            hist_mtime = hist_file.stat().st_mtime
            newest_mtime = newest.stat().st_mtime
            # If history session is within 60s of newest, prefer history
            if abs(hist_mtime - newest_mtime) < 60:
                newest = hist_file
                method += "+history_validated"

    return {
        "session_id": newest.stem,
        "claude_pid": claude_pid,
        "project_dir": ctx["cwd"],
        "transcript_path": str(newest),
        "anchor_uuid": ctx.get("anchor_uuid"),
        "pane": pane,
        "method": f"{method}+mtime",
    }


def _pid_cwd(pid):
    """Get the CWD for a PID via lsof."""
    output = _run(["lsof", "-p", str(pid), "-a", "-d", "cwd"])
    if output:
        for line in output.splitlines():
            if " cwd " in line:
                parts = line.split()
                return parts[-1] if parts else None
    return None


def resolve_all_sessions():
    """
    Resolve all active Claude sessions across tmux panes.

    Returns list of dicts (same format as resolve_session).
    """
    results = []
    seen_pids = set()

    # Method 1: tmux panes
    output = _run(["tmux", "list-panes", "-a", "-F", "#{pane_id} #{pane_pid}"])
    if output:
        for line in output.splitlines():
            parts = line.split()
            if len(parts) != 2:
                continue
            pane_id, shell_pid_str = parts
            try:
                shell_pid = int(shell_pid_str)
            except ValueError:
                continue

            claude_pid = _find_claude_child(shell_pid)
            if claude_pid and claude_pid not in seen_pids:
                seen_pids.add(claude_pid)
                result = resolve_session(pid=claude_pid, pane=pane_id)
                if result:
                    results.append(result)

    # Method 2: any Claude PIDs not found via tmux
    for pid in _get_all_claude_pids():
        if pid not in seen_pids:
            seen_pids.add(pid)
            result = resolve_session(pid=pid)
            if result:
                results.append(result)

    # Sort by project dir
    results.sort(key=lambda r: r.get("project_dir", ""))
    return results


def main():
    parser = argparse.ArgumentParser(
        prog="session-resolver",
        description="Resolve Claude Code session from execution context.",
    )
    parser.add_argument(
        "--pane",
        help="Tmux pane ID (e.g., %%94)",
    )
    parser.add_argument(
        "--pid",
        type=int,
        help="Explicit Claude process PID",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Resolve all active Claude sessions",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if args.all:
        results = resolve_all_sessions()
        if not results:
            print("No active Claude sessions found.", file=sys.stderr)
            sys.exit(1)

        if args.json_output:
            print(json.dumps(results, indent=2))
        else:
            print(f"{'Pane':<8} {'PID':>6} {'Project':<40} {'Session':>14} {'Method'}")
            print("-" * 90)
            for r in results:
                pane = r.get("pane") or "—"
                pid = r.get("claude_pid") or "—"
                proj = r.get("project_dir", "")
                # Shorten project path
                home = os.path.expanduser("~")
                if proj.startswith(home):
                    proj = "~" + proj[len(home):]
                proj = proj[:38]
                sid = r.get("session_id", "?")[:12] + "..."
                method = r.get("method", "?")
                print(f"{pane:<8} {str(pid):>6} {proj:<40} {sid:>14} {method}")
        sys.exit(0)

    # Single session resolution
    result = resolve_session(pid=args.pid, pane=args.pane)
    if not result:
        print("Error: Could not resolve Claude session.", file=sys.stderr)
        print("  Ensure you're running inside a Claude tool call,", file=sys.stderr)
        print("  or specify --pane or --pid.", file=sys.stderr)
        sys.exit(1)

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Session:  {result['session_id']}")
        print(f"PID:      {result.get('claude_pid') or '—'}")
        print(f"Project:  {result.get('project_dir', '—')}")
        print(f"Transcript: {result.get('transcript_path', '—')}")
        if result.get("anchor_uuid"):
            print(f"Anchor:   {result['anchor_uuid']}")
        if result.get("pane"):
            print(f"Pane:     {result['pane']}")
        print(f"Method:   {result.get('method', '—')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
