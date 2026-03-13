"""Integration tests: run understand against the mobile-terminal corpus."""

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "clogs"))
from understand import analyze_session
from gauge import extract_usage, compute_metrics


CORPUS = Path.home() / ".claude/projects/-Users-kd-Code-mobile-terminal"


@pytest.fixture(scope="module")
def corpus_files():
    files = list(CORPUS.glob("*.jsonl"))
    assert len(files) > 0, f"No JSONL files found in {CORPUS}"
    return files


def test_all_transcripts_parse(corpus_files):
    """AC-6: All mobile-terminal transcripts parse without errors."""
    errors = []
    empty = 0
    for f in corpus_files:
        try:
            state = analyze_session(str(f))
            if state is None:
                empty += 1
                continue
            # Validate JSON serializable
            json.dumps(state)
        except Exception as e:
            errors.append(f"{f.name}: {e}")

    assert not errors, f"Parse errors:\n" + "\n".join(errors)
    assert empty <= 5, f"Too many empty transcripts: {empty}"


def test_phase_diversity(corpus_files):
    """AC-3: At least 3 distinct phases detected across corpus."""
    phases = set()
    for f in corpus_files:
        state = analyze_session(str(f))
        if state:
            phases.add(state["phase"]["current"])

    assert len(phases) >= 3, f"Only {len(phases)} phases found: {phases}"


def test_json_schema(corpus_files):
    """AC-2/AC-8: JSON output has required fields and is stable."""
    # Pick a non-empty transcript
    for f in sorted(corpus_files, key=lambda p: p.stat().st_size, reverse=True)[:5]:
        state = analyze_session(str(f))
        if not state:
            continue

        # Required top-level keys
        assert "session_id" in state
        assert "phase" in state
        assert "health" in state
        assert "context" in state
        assert "activity" in state
        assert "intent" in state

        # Phase structure
        assert "current" in state["phase"]
        assert "confidence" in state["phase"]

        # Health structure
        assert "error_rate" in state["health"]
        assert "stuck" in state["health"]
        assert isinstance(state["health"]["stuck"], bool)

        # Context structure
        assert "current_size" in state["context"]
        assert "pct_used" in state["context"]
        assert "threshold" in state["context"]
        assert "compression_count" in state["context"]

        # Activity structure
        assert "files_read" in state["activity"]
        assert "tools_used" in state["activity"]
        assert isinstance(state["activity"]["tools_used"], dict)

        return  # one good validation is enough

    pytest.fail("No non-empty transcripts found for schema validation")


def test_context_matches_gauge(corpus_files):
    """AC-5: Context metrics match gauge.py output.

    current_size and pct_used should match exactly. burn_rate may differ
    slightly because gauge reads every streaming chunk while the parser
    merges chunks by message.id, yielding a slightly different turn count.
    """
    for f in sorted(corpus_files, key=lambda p: p.stat().st_size, reverse=True)[:3]:
        state = analyze_session(str(f))
        if not state:
            continue

        usage = extract_usage(str(f))
        gauge = compute_metrics(usage) if usage else None
        if not gauge:
            continue

        assert state["context"]["current_size"] == gauge["current_size"]
        assert state["context"]["pct_used"] == gauge["pct_used"]


def test_large_file_performance(corpus_files):
    """NFR-1: 21MB file parses in under 5 seconds."""
    largest = max(corpus_files, key=lambda p: p.stat().st_size)
    start = time.time()
    state = analyze_session(str(largest))
    elapsed = time.time() - start
    assert elapsed < 5.0, f"Parsing {largest.name} took {elapsed:.2f}s (limit: 5s)"
    assert state is not None
