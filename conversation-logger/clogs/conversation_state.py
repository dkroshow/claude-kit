"""
Conversation state extraction for Claude Code sessions.

Analyzes parsed transcript data to determine conversation phase,
health indicators, activity summary, and user intent. Designed
for consumption by the james meta-agent.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any

# Tool categories for phase detection
EXPLORE_TOOLS = frozenset(("Read", "Grep", "Glob"))
MODIFY_TOOLS = frozenset(("Edit", "Write"))
PLAN_TOOLS = frozenset(("Skill", "TaskCreate", "Task"))
AGENT_TOOLS = frozenset(("Task", "Agent"))


def detect_phase(messages: List[Dict], window: int = 20, live: bool = False) -> Dict[str, str]:
    """
    Classify the current conversation phase based on recent tool call patterns.

    Analyzes the last `window` messages to determine what the session is doing
    right now. Sessions are iterative (not linear pipelines), so this captures
    the current activity window.

    Args:
        messages: parsed message list from parse_transcript()
        window: number of recent messages to analyze
        live: if True, check for idle state (session is currently active).
              if False, always analyze tool patterns (historical analysis).

    Returns: {"current": phase_name, "confidence": "high"|"medium"|"low"}
    """
    if not messages:
        return {"current": "unknown", "confidence": "low"}

    # Check idle only for live sessions
    if live:
        last_msg = messages[-1]
        last_ts = _parse_timestamp(last_msg.get("timestamp"))
        if last_ts:
            idle_secs = time.time() - last_ts.timestamp()
            if idle_secs > 300:  # 5 minutes
                return {"current": "idle", "confidence": "high"}

    # Collect tool calls from recent window
    recent = messages[-window:]
    tool_counts = {}
    total_tools = 0

    for msg in recent:
        for tc in msg.get("tool_calls", []):
            name = tc.get("tool_name", "unknown")
            tool_counts[name] = tool_counts.get(name, 0) + 1
            total_tools += 1

    if total_tools == 0:
        # No tools in recent window — likely text-only conversation
        return {"current": "unknown", "confidence": "low"}

    # Categorize tools
    explore_count = sum(tool_counts.get(t, 0) for t in EXPLORE_TOOLS)
    modify_count = sum(tool_counts.get(t, 0) for t in MODIFY_TOOLS)
    bash_count = tool_counts.get("Bash", 0)
    plan_count = sum(tool_counts.get(t, 0) for t in PLAN_TOOLS)
    impl_count = modify_count + bash_count

    explore_pct = explore_count / total_tools
    modify_pct = modify_count / total_tools
    impl_pct = impl_count / total_tools

    # Planning: Skill/TaskCreate/Task activity present
    if plan_count >= 2:
        confidence = "high" if plan_count >= 3 else "medium"
        return {"current": "planning", "confidence": confidence}

    # Implementation: Edit/Write/Bash dominant
    if impl_pct > 0.5:
        confidence = "high" if total_tools > 5 else "medium"
        return {"current": "implementation", "confidence": confidence}

    # Exploration: Read/Grep/Glob dominant, low modification
    if explore_pct > 0.6 and modify_pct < 0.2:
        confidence = "high" if total_tools > 10 else "medium"
        return {"current": "exploration", "confidence": confidence}

    return {"current": "unknown", "confidence": "low"}


def assess_health(messages: List[Dict], tool_results: Dict, window: int = 10) -> Dict[str, Any]:
    """
    Assess conversation health: error rate, retry loops, stuck detection.

    Returns dict with error_rate, retry_loops, last_activity, idle_seconds, stuck.
    """
    now = time.time()
    last_activity = None
    idle_seconds = None

    if messages:
        last_ts = _parse_timestamp(messages[-1].get("timestamp"))
        if last_ts:
            last_activity = messages[-1]["timestamp"]
            idle_seconds = int(now - last_ts.timestamp())

    # Collect recent tool calls by iterating backwards until we have enough
    recent_calls = []
    for msg in reversed(messages):
        for tc in reversed(msg.get("tool_calls", [])):
            tool_use_id = tc.get("tool_use_id", "")
            result = tool_results.get(tool_use_id, {})
            recent_calls.append({
                "tool_name": tc.get("tool_name"),
                "input": tc.get("input"),
                "is_error": result.get("is_error", False),
            })
            if len(recent_calls) >= window:
                break
        if len(recent_calls) >= window:
            break
    recent_calls.reverse()  # restore chronological order

    # Error rate
    error_count = sum(1 for c in recent_calls if c["is_error"])
    error_rate = error_count / len(recent_calls) if recent_calls else 0.0

    # Retry loops: consecutive calls with same tool_name + same input
    retry_loops = 0
    if len(recent_calls) >= 2:
        streak = 1
        for i in range(1, len(recent_calls)):
            prev, curr = recent_calls[i - 1], recent_calls[i]
            if prev["tool_name"] == curr["tool_name"] and prev["input"] == curr["input"]:
                streak += 1
            else:
                if streak >= 3:
                    retry_loops += 1
                streak = 1
        if streak >= 3:
            retry_loops += 1

    stuck = error_rate > 0.5 or retry_loops >= 1

    return {
        "error_rate": round(error_rate, 3),
        "retry_loops": retry_loops,
        "last_activity": last_activity,
        "idle_seconds": idle_seconds,
        "stuck": stuck,
    }


def summarize_activity(messages: List[Dict]) -> Dict[str, Any]:
    """
    Summarize what the session has done: files touched, commands run, tools used.
    """
    files_read = set()
    files_edited = set()
    commands = []
    tools_used = {}
    agents_spawned = 0

    for msg in messages:
        for tc in msg.get("tool_calls", []):
            name = tc.get("tool_name", "unknown")
            tools_used[name] = tools_used.get(name, 0) + 1
            inp = tc.get("input") or {}

            if name == "Read":
                path = inp.get("file_path")
                if path:
                    files_read.add(path)
            elif name in MODIFY_TOOLS:
                path = inp.get("file_path")
                if path:
                    files_edited.add(path)
            elif name == "Bash":
                cmd = inp.get("command", "")
                if cmd:
                    commands.append(cmd[:80])
            elif name in AGENT_TOOLS:
                agents_spawned += 1

    return {
        "files_read": sorted(files_read),
        "files_edited": sorted(files_edited),
        "commands_run": commands[-20:],  # last 20
        "tools_used": tools_used,
        "agents_spawned": agents_spawned,
    }


def extract_intent(messages: List[Dict]) -> Dict[str, Any]:
    """
    Extract user intent from human messages.

    Uses first and latest human messages as proxy for task intent.
    """
    human_messages = [m for m in messages if m.get("is_human")]

    initial = None
    latest = None

    if human_messages:
        initial = (human_messages[0].get("content") or "")[:500]
        latest = (human_messages[-1].get("content") or "")[:500]

    return {
        "initial_prompt": initial,
        "latest_prompt": latest,
        "turn_count": len(human_messages),
    }


def _parse_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 timestamp string to datetime."""
    if not ts_str:
        return None
    try:
        # Handle both Z suffix and +00:00
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None
