# Session Resolver: Process-Level Signals for Claude Code

**Type:** gotcha
**Tags:** session-resolver, claude-code, lsof, tmux, process, macOS
**Created:** 2026-03-08

## Findings

### Anchor UUIDs are version-dependent
- Claude ≤v2.1.66: keeps `~/.claude/tasks/<uuid>/` open as a DIR fd (visible via `lsof`)
- Claude ≥v2.1.68: does NOT keep tasks/ open. No anchor UUID available.
- This means anchor-based session disambiguation only works for older versions.

### pgrep -P fails silently on macOS
- `pgrep -P <ppid>` returns exit code 1 even when children exist
- Use `ps -eo pid,ppid,comm` with filtering instead

### PPID walk works reliably
- From inside a Claude tool call: `os.getpid()` → walk up via `ps -o ppid=` → find process named `claude`
- Confirmed chain: shell (zsh) → claude → zsh (tool shell)

### Multi-session disambiguation limitations
- Without anchors, multiple Claude processes in the same CWD all resolve to the newest JSONL by mtime
- history.jsonl doesn't record which PID wrote each entry
- Claude doesn't expose session ID as an env var (only `CLAUDECODE=1`)
- Fundamental upstream limitation — no per-process session identifier in newer Claude versions

### Slug derivation confirmed
- Full absolute path with `/` replaced by `-`
- `/Users/kd/claude-kit` → `-Users-kd-claude-kit`
- Reversing slug to path is ambiguous (`claude-kit` vs `claude/kit`), use CWD directly
