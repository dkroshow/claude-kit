"""
Parse Claude Code JSONL transcripts into structured data for database ingestion.

Handles the streaming format where a single assistant turn produces multiple
JSONL lines (one per content block) sharing the same message.id.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime


def _clean_text(text):
    """Strip terminal artifacts from text."""
    if not text:
        return text
    # Strip ASCII control characters (NAK \x15, etc.) but keep newlines/tabs
    return text.replace("\x15", "").replace("\x00", "")


def _classify_human(role, content, is_tool_result):
    """Determine if a message is a real human/assistant conversational message."""
    if is_tool_result:
        return False
    if not content or len(content.strip()) < 2:
        return False
    if role == "user":
        if content.startswith("<command-"):
            return False
        if content.startswith("<local-command-"):
            return False
        if content.startswith("[Request interrupted"):
            return False
        # Expanded skill/command prompts
        lines = content.split("\n", 3)
        if len(lines) >= 3 and lines[0].startswith("# ") and lines[2].startswith("**Purpose:**"):
            return False
    return True


def extract_text_content(content):
    """Extract text from various content formats."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    if isinstance(content, dict):
        if content.get("type") == "text":
            return content.get("text", "")
        return str(content)
    return str(content) if content else ""


def extract_thinking(content):
    """Extract thinking blocks from assistant content."""
    if not isinstance(content, list):
        return None
    parts = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "thinking":
            thinking = item.get("thinking", "")
            if thinking:
                parts.append(thinking)
    return "\n".join(parts) if parts else None


def extract_tool_calls(content):
    """Extract tool_use blocks from assistant content."""
    if not isinstance(content, list):
        return []
    calls = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "tool_use":
            calls.append({
                "tool_use_id": item.get("id", ""),
                "tool_name": item.get("name", "unknown"),
                "input": item.get("input"),
            })
    return calls


def extract_tool_results(content):
    """Extract tool_result blocks from user content. Returns dict mapping tool_use_id -> result."""
    if not isinstance(content, list):
        return {}
    results = {}
    for item in content:
        if isinstance(item, dict) and item.get("type") == "tool_result":
            tool_use_id = item.get("tool_use_id", "")
            if tool_use_id:
                result_content = item.get("content", "")
                if isinstance(result_content, list):
                    # Sometimes content is a list of blocks
                    parts = []
                    for block in result_content:
                        if isinstance(block, dict):
                            parts.append(block.get("text", str(block)))
                        else:
                            parts.append(str(block))
                    result_content = "\n".join(parts)
                results[tool_use_id] = {
                    "content": str(result_content) if result_content else "",
                    "is_error": bool(item.get("is_error", False)),
                }
    return results


def parse_transcript(filepath):
    """
    Parse a JSONL transcript file into structured data.

    Returns dict with:
        session: dict of session-level metadata
        messages: list of parsed message dicts (user + merged assistant turns)
        tool_results: dict mapping tool_use_id -> result data
        turn_durations: dict mapping parent_uuid -> duration_ms
    """
    entries = []
    turn_durations = {}

    path = Path(filepath)
    if not path.exists():
        print(f"Warning: transcript not found: {filepath}", file=sys.stderr)
        return None

    # Derive project slug from path: ~/.claude/projects/<slug>/<uuid>.jsonl
    project_slug = None
    transcript_path = str(path)
    parts = path.parts
    try:
        projects_idx = parts.index("projects")
        if projects_idx + 1 < len(parts):
            project_slug = parts[projects_idx + 1]
    except ValueError:
        pass

    with open(filepath, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print(f"Warning: malformed JSON at line {line_num} in {filepath}", file=sys.stderr)
                continue

            entry_type = entry.get("type")

            if entry_type in ("user", "assistant"):
                entries.append(entry)
            elif entry_type == "system" and entry.get("subtype") == "turn_duration":
                parent = entry.get("parentUuid")
                if parent:
                    turn_durations[parent] = entry.get("durationMs")

    if not entries:
        return None

    # Extract session metadata from first entry
    first = entries[0]
    session_id = first.get("sessionId", path.stem)
    session = {
        "session_id": session_id,
        "transcript_path": transcript_path,
        "project_path": first.get("cwd"),
        "project_slug": project_slug,
        "git_branch": first.get("gitBranch"),
        "claude_version": first.get("version"),
        "permission_mode": first.get("permissionMode"),
        "model": None,  # Set from first assistant message
    }

    # Group assistant entries by message.id (streaming chunks share the same msg id)
    # User entries are 1:1 with JSONL lines
    messages = []
    tool_results = {}
    assistant_groups = {}  # message.id -> list of entries

    for entry in entries:
        entry_type = entry.get("type")

        if entry_type == "user":
            content_raw = entry.get("message", {}).get("content", "")

            # Check if this is a tool_result user message
            results = extract_tool_results(content_raw)
            if results:
                tool_results.update(results)
                # Tool result messages are synthetic — still store them but with result content
                text = ""
                for r in results.values():
                    if r["content"]:
                        text += r["content"] + "\n"
                text = text.strip()
            else:
                text = extract_text_content(content_raw)

            if not text.strip() and not results:
                continue

            cleaned = _clean_text(text.strip()) if text else None
            is_tr = bool(results)
            messages.append({
                "message_uuid": entry.get("uuid", ""),
                "parent_uuid": entry.get("parentUuid"),
                "role": "user",
                "content": cleaned,
                "thinking": None,
                "model": None,
                "stop_reason": None,
                "input_tokens": None,
                "output_tokens": None,
                "cache_read_input_tokens": None,
                "cache_creation_input_tokens": None,
                "is_sidechain": bool(entry.get("isSidechain", False)),
                "cwd": entry.get("cwd"),
                "timestamp": entry.get("timestamp"),
                "turn_duration_ms": None,
                "tool_calls": [],
                "is_tool_result": is_tr,
                "is_human": _classify_human("user", cleaned, is_tr),
            })

        elif entry_type == "assistant":
            msg = entry.get("message", {})
            msg_id = msg.get("id", entry.get("uuid", ""))

            if msg_id not in assistant_groups:
                assistant_groups[msg_id] = []
            assistant_groups[msg_id].append(entry)

    # Merge assistant groups into single messages
    for msg_id, group in assistant_groups.items():
        # Merge all content blocks
        all_content = []
        for entry in group:
            content = entry.get("message", {}).get("content", [])
            if isinstance(content, list):
                all_content.extend(content)

        text = extract_text_content(all_content)
        thinking = extract_thinking(all_content)
        tool_calls = extract_tool_calls(all_content)

        # Take metadata from the first entry in the group
        first_entry = group[0]
        msg = first_entry.get("message", {})
        usage = msg.get("usage", {})
        last_entry = group[-1]

        # Set session model from first assistant message
        if session["model"] is None:
            session["model"] = msg.get("model")

        # Find the last uuid in the group for turn_duration lookup
        last_uuid = last_entry.get("uuid", "")
        duration = turn_durations.get(last_uuid)

        cleaned = _clean_text(text.strip()) if text else None
        messages.append({
            "message_uuid": msg_id,
            "parent_uuid": first_entry.get("parentUuid"),
            "role": "assistant",
            "content": cleaned,
            "thinking": thinking,
            "model": msg.get("model"),
            "stop_reason": msg.get("stop_reason"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
            "is_sidechain": bool(first_entry.get("isSidechain", False)),
            "cwd": first_entry.get("cwd"),
            "timestamp": first_entry.get("timestamp"),
            "turn_duration_ms": duration,
            "tool_calls": tool_calls,
            "is_tool_result": False,
            "is_human": _classify_human("assistant", cleaned, False),
        })

    # Sort messages by timestamp
    messages.sort(key=lambda m: m.get("timestamp") or "")

    # Derive session timestamps
    timestamps = [m["timestamp"] for m in messages if m.get("timestamp")]
    if timestamps:
        session["started_at"] = timestamps[0]
        session["ended_at"] = timestamps[-1]

    return {
        "session": session,
        "messages": messages,
        "tool_results": tool_results,
    }
