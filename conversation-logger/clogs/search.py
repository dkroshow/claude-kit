"""
Search and analytics helpers for Claude conversation data.

Provides functions for full-text search, analytics queries, and
meta-agent access patterns.
"""

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
