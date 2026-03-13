"""Unit tests for conversation state extraction."""

import time
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "clogs"))
from conversation_state import detect_phase, assess_health, summarize_activity, extract_intent


def _make_msg(role="assistant", is_human=False, tool_calls=None, content=None, timestamp=None):
    """Helper to create a minimal message dict."""
    return {
        "role": role,
        "is_human": is_human,
        "content": content,
        "tool_calls": tool_calls or [],
        "timestamp": timestamp,
    }


def _make_tc(name, input=None, tool_use_id=None):
    """Helper to create a tool call dict."""
    return {
        "tool_name": name,
        "input": input or {},
        "tool_use_id": tool_use_id or f"tool_{name}_{id(input)}",
    }


class TestDetectPhase:
    def test_empty_messages(self):
        assert detect_phase([]) == {"current": "unknown", "confidence": "low"}

    def test_no_tools(self):
        msgs = [_make_msg(content="hello")] * 5
        assert detect_phase(msgs)["current"] == "unknown"

    def test_implementation_phase(self):
        msgs = [
            _make_msg(tool_calls=[_make_tc("Edit", {"file_path": "a.py"})]),
            _make_msg(tool_calls=[_make_tc("Bash", {"command": "npm test"})]),
            _make_msg(tool_calls=[_make_tc("Write", {"file_path": "b.py"})]),
            _make_msg(tool_calls=[_make_tc("Edit", {"file_path": "a.py"})]),
            _make_msg(tool_calls=[_make_tc("Bash", {"command": "npm test"})]),
            _make_msg(tool_calls=[_make_tc("Bash", {"command": "git diff"})]),
        ]
        phase = detect_phase(msgs)
        assert phase["current"] == "implementation"
        assert phase["confidence"] == "high"

    def test_exploration_phase(self):
        msgs = [
            _make_msg(tool_calls=[_make_tc("Read", {"file_path": "a.py"})]),
            _make_msg(tool_calls=[_make_tc("Grep", {"pattern": "foo"})]),
            _make_msg(tool_calls=[_make_tc("Glob", {"pattern": "*.py"})]),
            _make_msg(tool_calls=[_make_tc("Read", {"file_path": "b.py"})]),
            _make_msg(tool_calls=[_make_tc("Grep", {"pattern": "bar"})]),
            _make_msg(tool_calls=[_make_tc("Read", {"file_path": "c.py"})]),
            _make_msg(tool_calls=[_make_tc("Read", {"file_path": "d.py"})]),
            _make_msg(tool_calls=[_make_tc("Grep", {"pattern": "baz"})]),
            _make_msg(tool_calls=[_make_tc("Glob", {"pattern": "src/**"})]),
            _make_msg(tool_calls=[_make_tc("Read", {"file_path": "e.py"})]),
            _make_msg(tool_calls=[_make_tc("Read", {"file_path": "f.py"})]),
        ]
        phase = detect_phase(msgs)
        assert phase["current"] == "exploration"
        assert phase["confidence"] == "high"

    def test_planning_phase(self):
        msgs = [
            _make_msg(tool_calls=[_make_tc("Skill", {"skill": "_plan"})]),
            _make_msg(tool_calls=[_make_tc("TaskCreate")]),
            _make_msg(tool_calls=[_make_tc("TaskCreate")]),
        ]
        phase = detect_phase(msgs)
        assert phase["current"] == "planning"

    def test_idle_only_when_live(self):
        old_ts = "2020-01-01T00:00:00Z"
        msgs = [_make_msg(tool_calls=[_make_tc("Edit")], timestamp=old_ts)]
        # live=False: should analyze tools, not time
        phase = detect_phase(msgs, live=False)
        assert phase["current"] != "idle"
        # live=True: should detect idle
        phase = detect_phase(msgs, live=True)
        assert phase["current"] == "idle"


class TestAssessHealth:
    def test_healthy_session(self):
        msgs = [_make_msg(tool_calls=[_make_tc("Read", tool_use_id="t1")])]
        tool_results = {"t1": {"is_error": False, "content": "ok"}}
        health = assess_health(msgs, tool_results)
        assert health["error_rate"] == 0.0
        assert health["retry_loops"] == 0
        assert health["stuck"] is False

    def test_high_error_rate(self):
        tcs = [_make_tc("Bash", {"command": f"cmd{i}"}, tool_use_id=f"t{i}") for i in range(10)]
        msgs = [_make_msg(tool_calls=[tc]) for tc in tcs]
        tool_results = {f"t{i}": {"is_error": i < 6, "content": ""} for i in range(10)}
        health = assess_health(msgs, tool_results)
        assert health["error_rate"] == 0.6
        assert health["stuck"] is True

    def test_retry_loop_detection(self):
        same_input = {"command": "npm test"}
        tcs = [_make_tc("Bash", same_input, tool_use_id=f"t{i}") for i in range(5)]
        msgs = [_make_msg(tool_calls=[tc]) for tc in tcs]
        tool_results = {f"t{i}": {"is_error": False, "content": ""} for i in range(5)}
        health = assess_health(msgs, tool_results)
        assert health["retry_loops"] >= 1
        assert health["stuck"] is True


class TestSummarizeActivity:
    def test_file_tracking(self):
        msgs = [
            _make_msg(tool_calls=[_make_tc("Read", {"file_path": "/a.py"})]),
            _make_msg(tool_calls=[_make_tc("Edit", {"file_path": "/b.py"})]),
            _make_msg(tool_calls=[_make_tc("Write", {"file_path": "/c.py"})]),
            _make_msg(tool_calls=[_make_tc("Bash", {"command": "npm test"})]),
            _make_msg(tool_calls=[_make_tc("Task", {"prompt": "explore"})]),
        ]
        activity = summarize_activity(msgs)
        assert "/a.py" in activity["files_read"]
        assert "/b.py" in activity["files_edited"]
        assert "/c.py" in activity["files_edited"]
        assert "npm test" in activity["commands_run"]
        assert activity["agents_spawned"] == 1
        assert activity["tools_used"]["Read"] == 1
        assert activity["tools_used"]["Edit"] == 1


class TestExtractIntent:
    def test_basic_intent(self):
        msgs = [
            _make_msg(role="user", is_human=True, content="Fix the login bug"),
            _make_msg(role="assistant", is_human=True, content="Looking at the code..."),
            _make_msg(role="user", is_human=True, content="Now run the tests"),
        ]
        intent = extract_intent(msgs)
        assert intent["initial_prompt"] == "Fix the login bug"
        assert intent["latest_prompt"] == "Now run the tests"
        assert intent["turn_count"] == 3

    def test_no_human_messages(self):
        msgs = [_make_msg(role="user", is_human=False, content="tool result")]
        intent = extract_intent(msgs)
        assert intent["initial_prompt"] is None
        assert intent["turn_count"] == 0
