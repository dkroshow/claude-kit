"""
Search and analytics helpers for Claude conversation data.

Provides functions for full-text search, analytics queries, and
meta-agent access patterns.

CLI usage:
    python3 search.py search <query> [--limit N]
    python3 search.py recent [--project SLUG] [--limit N]
    python3 search.py session <session-id>
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from clogs.db import get_connection


def search_messages(query, limit=20):
    """Full-text search across all conversations. Returns ranked results."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, s.session_id, m.role, LEFT(m.content, 500) AS preview,
                   m.timestamp, s.project_slug, s.git_branch,
                   ts_rank(m.search_vector, websearch_to_tsquery('english', %(query)s)) AS rank
            FROM claude_messages m
            JOIN claude_sessions s ON s.id = m.session_id
            WHERE m.search_vector @@ websearch_to_tsquery('english', %(query)s)
            ORDER BY rank DESC
            LIMIT %(limit)s
        """, {"query": query, "limit": limit})
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def session_summary(session_id):
    """Get full summary of a session including metadata and message count."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.*,
                   (SELECT COUNT(*) FROM claude_messages m WHERE m.session_id = s.id) AS message_count,
                   (SELECT COUNT(*) FROM claude_tool_calls tc
                    JOIN claude_messages m ON m.id = tc.message_id
                    WHERE m.session_id = s.id) AS tool_call_count
            FROM claude_sessions s
            WHERE s.session_id = %(session_id)s
        """, {"session_id": session_id})
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None
    finally:
        conn.close()


def token_usage_by_day(days=30):
    """Token usage aggregated by day, most recent first."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                DATE(m.timestamp) AS day,
                COUNT(DISTINCT s.id) AS sessions,
                COUNT(*) FILTER (WHERE m.role = 'assistant') AS turns,
                SUM(m.input_tokens) AS input_tokens,
                SUM(m.output_tokens) AS output_tokens,
                SUM(m.cache_read_input_tokens) AS cache_read_tokens,
                SUM(m.cache_creation_input_tokens) AS cache_creation_tokens
            FROM claude_messages m
            JOIN claude_sessions s ON s.id = m.session_id
            WHERE m.timestamp > now() - make_interval(days => %(days)s)
            GROUP BY DATE(m.timestamp)
            ORDER BY day DESC
        """, {"days": days})
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def token_usage_by_project():
    """Token usage aggregated by project."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                s.project_slug,
                COUNT(DISTINCT s.id) AS sessions,
                SUM(s.total_input_tokens) AS input_tokens,
                SUM(s.total_output_tokens) AS output_tokens,
                SUM(s.total_turns) AS turns
            FROM claude_sessions s
            GROUP BY s.project_slug
            ORDER BY input_tokens DESC NULLS LAST
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def tool_usage_stats(limit=20):
    """Most frequently used tools across all sessions."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                tc.tool_name,
                COUNT(*) AS call_count,
                COUNT(DISTINCT s.id) AS session_count,
                COUNT(*) FILTER (WHERE tc.is_error) AS error_count
            FROM claude_tool_calls tc
            JOIN claude_messages m ON m.id = tc.message_id
            JOIN claude_sessions s ON s.id = m.session_id
            GROUP BY tc.tool_name
            ORDER BY call_count DESC
            LIMIT %(limit)s
        """, {"limit": limit})
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def recent_sessions(limit=10, project_slug=None):
    """List recent sessions with summary info."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if project_slug:
            cur.execute("""
                SELECT s.session_id, s.project_slug, s.git_branch, s.model,
                       s.started_at, s.ended_at, s.total_turns,
                       s.total_input_tokens, s.total_output_tokens,
                       (SELECT LEFT(m.content, 200) FROM claude_messages m
                        WHERE m.session_id = s.id AND m.role = 'user'
                        ORDER BY m.timestamp LIMIT 1) AS first_prompt
                FROM claude_sessions s
                WHERE s.project_slug = %(project_slug)s
                ORDER BY s.started_at DESC NULLS LAST
                LIMIT %(limit)s
            """, {"limit": limit, "project_slug": project_slug})
        else:
            cur.execute("""
                SELECT s.session_id, s.project_slug, s.git_branch, s.model,
                       s.started_at, s.ended_at, s.total_turns,
                       s.total_input_tokens, s.total_output_tokens,
                       (SELECT LEFT(m.content, 200) FROM claude_messages m
                        WHERE m.session_id = s.id AND m.role = 'user'
                        ORDER BY m.timestamp LIMIT 1) AS first_prompt
                FROM claude_sessions s
                ORDER BY s.started_at DESC NULLS LAST
                LIMIT %(limit)s
            """, {"limit": limit})
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


# --- CLI ---

def _fmt_timestamp(ts):
    """Format a timestamp for display."""
    if ts is None:
        return "—"
    s = str(ts)
    if "." in s:
        s = s.split(".")[0]
    return s


def _fmt_tokens(n):
    """Format token count with K/M suffix."""
    if n is None:
        return "—"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def cmd_search(args):
    query = " ".join(args.query)
    results = search_messages(query, limit=args.limit)
    if not results:
        print(f"No results for: {query}")
        return
    print(f"Found {len(results)} result(s) for: {query}\n")
    for i, r in enumerate(results, 1):
        print(f"--- Result {i} (rank: {r['rank']:.3f}) ---")
        print(f"  Session:  {r['session_id']}")
        print(f"  Project:  {r.get('project_slug') or '—'}")
        print(f"  Branch:   {r.get('git_branch') or '—'}")
        print(f"  Role:     {r['role']}")
        print(f"  Time:     {_fmt_timestamp(r.get('timestamp'))}")
        preview = (r.get("preview") or "").strip().replace("\n", "\n            ")
        print(f"  Preview:  {preview}")
        print()


def cmd_recent(args):
    results = recent_sessions(limit=args.limit, project_slug=args.project)
    if not results:
        print("No sessions found.")
        return
    print(f"{'Session ID':<40} {'Project':<25} {'Branch':<15} {'Started':<20} {'Turns':>6} {'Tokens':>10}")
    print("─" * 120)
    for r in results:
        sid = (r.get("session_id") or "—")[:38]
        proj = (r.get("project_slug") or "—")[:23]
        branch = (r.get("git_branch") or "—")[:13]
        started = _fmt_timestamp(r.get("started_at"))[:18]
        turns = str(r.get("total_turns") or 0)
        tokens = _fmt_tokens((r.get("total_input_tokens") or 0) + (r.get("total_output_tokens") or 0))
        print(f"{sid:<40} {proj:<25} {branch:<15} {started:<20} {turns:>6} {tokens:>10}")
        prompt = (r.get("first_prompt") or "").strip()
        if prompt:
            prompt = prompt.replace("\n", " ")[:80]
            print(f"  → {prompt}")


def cmd_session(args):
    result = session_summary(args.session_id)
    if not result:
        print(f"Session not found: {args.session_id}")
        sys.exit(1)
    print(f"Session: {result.get('session_id')}")
    print(f"  Project:      {result.get('project_slug') or '—'}")
    print(f"  Branch:       {result.get('git_branch') or '—'}")
    print(f"  Model:        {result.get('model') or '—'}")
    print(f"  Started:      {_fmt_timestamp(result.get('started_at'))}")
    print(f"  Ended:        {_fmt_timestamp(result.get('ended_at'))}")
    print(f"  Turns:        {result.get('total_turns') or 0}")
    print(f"  Messages:     {result.get('message_count') or 0}")
    print(f"  Tool calls:   {result.get('tool_call_count') or 0}")
    print(f"  Input tokens:  {_fmt_tokens(result.get('total_input_tokens'))}")
    print(f"  Output tokens: {_fmt_tokens(result.get('total_output_tokens'))}")


def main():
    parser = argparse.ArgumentParser(
        prog="clogs-search",
        description="Search Claude conversation history stored in PostgreSQL.",
    )
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Full-text search across conversations")
    p_search.add_argument("query", nargs="+", help="Search terms")
    p_search.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    p_recent = sub.add_parser("recent", help="List recent sessions")
    p_recent.add_argument("--project", help="Filter by project slug")
    p_recent.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    p_session = sub.add_parser("session", help="Show session details")
    p_session.add_argument("session_id", help="Claude session UUID")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {"search": cmd_search, "recent": cmd_recent, "session": cmd_session}
    dispatch[args.command](args)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        err_name = type(e).__name__
        if "OperationalError" in err_name or "Connection" in err_name.lower():
            print(f"Error: Cannot connect to database. Is PostgreSQL running on port 5434?\n  {e}", file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
