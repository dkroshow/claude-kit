"""
PostgreSQL connection and upsert operations for the Claude conversation logger.

Connects to PostgreSQL and provides idempotent upsert functions
for sessions, messages, and tool calls.
"""

import os
import json
import sys

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)


def _strip_nul(val):
    """Strip NUL (0x00) characters that PostgreSQL text columns reject."""
    if isinstance(val, str):
        return val.replace("\x00", "")
    return val


def get_connection():
    """Get a connection to the database. Requires DATABASE_URL env var."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("Error: DATABASE_URL environment variable is required.", file=sys.stderr)
        print("Example: export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'", file=sys.stderr)
        sys.exit(1)
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    return conn


def upsert_session(cur, session):
    """
    Insert or update a session record. Returns the database UUID for the session.

    Upserts on session_id (Claude Code's session UUID).
    """
    cur.execute("""
        INSERT INTO claude_sessions (
            session_id, transcript_path, project_path, project_slug,
            git_branch, claude_version, model, permission_mode,
            started_at, ended_at, compression_count, last_compressed_at
        ) VALUES (
            %(session_id)s, %(transcript_path)s, %(project_path)s, %(project_slug)s,
            %(git_branch)s, %(claude_version)s, %(model)s, %(permission_mode)s,
            %(started_at)s, %(ended_at)s, %(compression_count)s, %(last_compressed_at)s
        )
        ON CONFLICT (session_id) DO UPDATE SET
            transcript_path = EXCLUDED.transcript_path,
            project_path = COALESCE(EXCLUDED.project_path, claude_sessions.project_path),
            project_slug = COALESCE(EXCLUDED.project_slug, claude_sessions.project_slug),
            git_branch = COALESCE(EXCLUDED.git_branch, claude_sessions.git_branch),
            claude_version = COALESCE(EXCLUDED.claude_version, claude_sessions.claude_version),
            model = COALESCE(EXCLUDED.model, claude_sessions.model),
            permission_mode = COALESCE(EXCLUDED.permission_mode, claude_sessions.permission_mode),
            started_at = LEAST(EXCLUDED.started_at, claude_sessions.started_at),
            ended_at = GREATEST(EXCLUDED.ended_at, claude_sessions.ended_at),
            compression_count = COALESCE(EXCLUDED.compression_count, claude_sessions.compression_count),
            last_compressed_at = GREATEST(EXCLUDED.last_compressed_at, claude_sessions.last_compressed_at),
            updated_at = now()
        RETURNING id
    """, session)

    return cur.fetchone()[0]


def upsert_message(cur, session_db_id, msg):
    """
    Insert or update a message record. Returns the database UUID for the message.

    Upserts on message_uuid.
    """
    cur.execute("""
        INSERT INTO claude_messages (
            session_id, message_uuid, parent_uuid, role, content, thinking,
            model, stop_reason, input_tokens, output_tokens,
            cache_read_input_tokens, cache_creation_input_tokens,
            is_sidechain, is_tool_result, is_human, cwd, timestamp, turn_duration_ms
        ) VALUES (
            %(session_db_id)s, %(message_uuid)s, %(parent_uuid)s, %(role)s,
            %(content)s, %(thinking)s, %(model)s, %(stop_reason)s,
            %(input_tokens)s, %(output_tokens)s,
            %(cache_read_input_tokens)s, %(cache_creation_input_tokens)s,
            %(is_sidechain)s, %(is_tool_result)s, %(is_human)s, %(cwd)s, %(timestamp)s, %(turn_duration_ms)s
        )
        ON CONFLICT (message_uuid) DO UPDATE SET
            content = COALESCE(EXCLUDED.content, claude_messages.content),
            thinking = COALESCE(EXCLUDED.thinking, claude_messages.thinking),
            model = COALESCE(EXCLUDED.model, claude_messages.model),
            stop_reason = COALESCE(EXCLUDED.stop_reason, claude_messages.stop_reason),
            input_tokens = COALESCE(EXCLUDED.input_tokens, claude_messages.input_tokens),
            output_tokens = COALESCE(EXCLUDED.output_tokens, claude_messages.output_tokens),
            cache_read_input_tokens = COALESCE(EXCLUDED.cache_read_input_tokens, claude_messages.cache_read_input_tokens),
            cache_creation_input_tokens = COALESCE(EXCLUDED.cache_creation_input_tokens, claude_messages.cache_creation_input_tokens),
            turn_duration_ms = COALESCE(EXCLUDED.turn_duration_ms, claude_messages.turn_duration_ms),
            is_tool_result = EXCLUDED.is_tool_result,
            is_human = EXCLUDED.is_human,
            updated_at = now()
        RETURNING id
    """, {
        "session_db_id": session_db_id,
        "message_uuid": msg["message_uuid"],
        "parent_uuid": msg.get("parent_uuid"),
        "role": msg["role"],
        "content": _strip_nul(msg.get("content")),
        "thinking": _strip_nul(msg.get("thinking")),
        "model": msg.get("model"),
        "stop_reason": msg.get("stop_reason"),
        "input_tokens": msg.get("input_tokens"),
        "output_tokens": msg.get("output_tokens"),
        "cache_read_input_tokens": msg.get("cache_read_input_tokens"),
        "cache_creation_input_tokens": msg.get("cache_creation_input_tokens"),
        "is_sidechain": msg.get("is_sidechain", False),
        "is_tool_result": msg.get("is_tool_result", False),
        "is_human": msg.get("is_human", False),
        "cwd": msg.get("cwd"),
        "timestamp": msg.get("timestamp"),
        "turn_duration_ms": msg.get("turn_duration_ms"),
    })

    return cur.fetchone()[0]


def upsert_tool_call(cur, message_db_id, tool_call):
    """
    Insert or update a tool call record. Returns the database UUID.

    Upserts on tool_use_id.
    """
    input_json = None
    if tool_call.get("input") is not None:
        input_json = _strip_nul(json.dumps(tool_call["input"]))

    cur.execute("""
        INSERT INTO claude_tool_calls (
            message_id, tool_use_id, tool_name, input
        ) VALUES (
            %(message_db_id)s, %(tool_use_id)s, %(tool_name)s, %(input)s
        )
        ON CONFLICT (tool_use_id) DO UPDATE SET
            tool_name = EXCLUDED.tool_name,
            input = COALESCE(EXCLUDED.input, claude_tool_calls.input),
            updated_at = now()
        RETURNING id
    """, {
        "message_db_id": message_db_id,
        "tool_use_id": tool_call["tool_use_id"],
        "tool_name": tool_call["tool_name"],
        "input": input_json,
    })

    return cur.fetchone()[0]


def backfill_tool_results(cur, tool_results):
    """
    Update tool call records with their results.

    tool_results: dict mapping tool_use_id -> {"content": str, "is_error": bool}
    """
    for tool_use_id, result in tool_results.items():
        cur.execute("""
            UPDATE claude_tool_calls
            SET result_content = %(content)s,
                is_error = %(is_error)s,
                updated_at = now()
            WHERE tool_use_id = %(tool_use_id)s
        """, {
            "tool_use_id": tool_use_id,
            "content": _strip_nul(result.get("content")),
            "is_error": result.get("is_error", False),
        })


def update_session_aggregates(cur, session_db_id):
    """Recalculate aggregate token counts and turn count for a session."""
    cur.execute("""
        UPDATE claude_sessions SET
            total_input_tokens = COALESCE(sub.total_input, 0),
            total_output_tokens = COALESCE(sub.total_output, 0),
            total_cache_read_tokens = COALESCE(sub.total_cache_read, 0),
            total_cache_creation_tokens = COALESCE(sub.total_cache_creation, 0),
            total_turns = COALESCE(sub.turn_count, 0),
            updated_at = now()
        FROM (
            SELECT
                SUM(input_tokens) AS total_input,
                SUM(output_tokens) AS total_output,
                SUM(cache_read_input_tokens) AS total_cache_read,
                SUM(cache_creation_input_tokens) AS total_cache_creation,
                COUNT(*) FILTER (WHERE role = 'assistant') AS turn_count
            FROM claude_messages
            WHERE session_id = %(session_db_id)s
        ) sub
        WHERE claude_sessions.id = %(session_db_id)s
    """, {"session_db_id": session_db_id})


def ingest_transcript(parsed_data):
    """
    Ingest a parsed transcript into the database.

    parsed_data: output from parser.parse_transcript()
    Returns dict with counts of records upserted.
    """
    if not parsed_data:
        return {"sessions": 0, "messages": 0, "tool_calls": 0, "tool_results": 0}

    session = parsed_data["session"]
    messages = parsed_data["messages"]
    tool_results = parsed_data["tool_results"]

    conn = get_connection()
    try:
        cur = conn.cursor()

        # Upsert session
        session_db_id = upsert_session(cur, session)

        # Upsert messages and their tool calls
        msg_count = 0
        tc_count = 0
        for msg in messages:
            msg_db_id = upsert_message(cur, session_db_id, msg)
            msg_count += 1

            for tc in msg.get("tool_calls", []):
                upsert_tool_call(cur, msg_db_id, tc)
                tc_count += 1

        # Backfill tool results
        tr_count = len(tool_results)
        if tool_results:
            backfill_tool_results(cur, tool_results)

        # Update session aggregates
        update_session_aggregates(cur, session_db_id)

        conn.commit()
        return {
            "sessions": 1,
            "messages": msg_count,
            "tool_calls": tc_count,
            "tool_results": tr_count,
        }

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
