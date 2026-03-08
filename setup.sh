#!/bin/bash
# claude-kit Global Setup
# Installs commands, agents, hooks, skills, and rules to ~/.claude/
# Detects and replaces any existing agentic-project-init installation.
#
# Usage:
#   ./setup.sh [--dry-run]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR"  # Flat structure — repo root IS the source

VERSION=$(git -C "$SOURCE_DIR" describe --tags 2>/dev/null || git -C "$SOURCE_DIR" rev-parse --short HEAD 2>/dev/null || echo "unknown")

DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--dry-run]"
            echo ""
            echo "Options:"
            echo "  --dry-run  Show what would be done without making changes"
            echo "  -h, --help Show this help message"
            exit 0
            ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

TARGET_DIR="$HOME/.claude"

create_symlink() {
    local source="$1"
    local target="$2"
    local name="$3"

    if [ "$DRY_RUN" = true ]; then
        if [ -e "$target" ]; then
            echo -e "${YELLOW}[DRY RUN] Would replace: $name${NC}"
        else
            echo -e "${GREEN}[DRY RUN] Would create: $target -> $source${NC}"
        fi
        return
    fi

    if [ -L "$target" ]; then
        rm "$target"
        ln -s "$source" "$target"
        echo -e "${GREEN}  + $name${NC}"
    elif [ -e "$target" ]; then
        echo -e "${YELLOW}  ! File exists (not symlink): $name${NC}"
    else
        ln -s "$source" "$target"
        echo -e "${GREEN}  + $name${NC}"
    fi
}

create_dir() {
    local dir="$1"
    if [ "$DRY_RUN" = true ]; then
        [ ! -d "$dir" ] && echo -e "${BLUE}[DRY RUN] Would create: $dir${NC}"
    else
        mkdir -p "$dir"
    fi
}

echo -e "${GREEN}claude-kit Setup${NC}"
echo "================"
[ "$DRY_RUN" = true ] && echo -e "${YELLOW}[DRY RUN MODE]${NC}"
echo ""

# Verify source exists (flat structure — check for commands/ at repo root)
if [ ! -d "$SOURCE_DIR/commands" ]; then
    echo -e "${RED}Error: commands/ not found at $SOURCE_DIR${NC}"
    echo "Are you running this from the claude-kit repo root?"
    exit 1
fi

# --- Takeover: remove agentic-project-init remnants ---
cleanup_agentic() {
    local cleaned=0

    # Remove symlinks pointing to agentic-project-init
    for subdir in commands agents hooks skills rules scripts; do
        [ -d "$TARGET_DIR/$subdir" ] || continue
        for file in "$TARGET_DIR/$subdir"/*; do
            [ -L "$file" ] || continue
            target=$(readlink "$file")
            if [[ "$target" == *"agentic-project-init"* ]]; then
                if [ "$DRY_RUN" = true ]; then
                    echo -e "${YELLOW}[DRY RUN] Would remove stale: $subdir/$(basename "$file")${NC}"
                else
                    rm "$file"
                    echo -e "${YELLOW}  - Removed stale: $subdir/$(basename "$file")${NC}"
                fi
                ((cleaned++)) || true
            fi
        done
    done

    # Remove old metadata files
    for file in .agentic-pack-source .agentic-pack-version; do
        if [ -f "$TARGET_DIR/$file" ]; then
            if [ "$DRY_RUN" = true ]; then
                echo -e "${YELLOW}[DRY RUN] Would remove: $file${NC}"
            else
                rm "$TARGET_DIR/$file"
                echo -e "${YELLOW}  - Removed: $file${NC}"
            fi
            ((cleaned++)) || true
        fi
    done

    if [ "$cleaned" -gt 0 ] || [ "$DRY_RUN" = true ]; then
        echo ""
    fi
}

echo "Checking for existing installations..."
cleanup_agentic

# Create directories
for subdir in commands agents hooks skills rules; do
    create_dir "$TARGET_DIR/$subdir"
done

# Create global learnings directory
create_dir "$TARGET_DIR/learnings"
if [ ! -f "$TARGET_DIR/learnings/index.md" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY RUN] Would create: learnings/index.md${NC}"
    else
        cat > "$TARGET_DIR/learnings/index.md" << 'EOF'
# Global Learning Index

> Machine-wide learnings that apply across all projects.
> Scanned by Claude at session start for relevant prior knowledge.

| Date | Type | Tags | Summary | File |
|------|------|------|---------|------|
EOF
        echo -e "${GREEN}  + learnings/index.md${NC}"
    fi
fi

# Symlink commands
echo ""
echo "Setting up commands..."
for file in "$SOURCE_DIR"/commands/*.md; do
    [ -f "$file" ] || continue
    filename=$(basename "$file")
    create_symlink "$file" "$TARGET_DIR/commands/$filename" "$filename"
done

# Symlink agents
echo ""
echo "Setting up agents..."
for file in "$SOURCE_DIR"/agents/*.md; do
    [ -f "$file" ] || continue
    filename=$(basename "$file")
    create_symlink "$file" "$TARGET_DIR/agents/$filename" "$filename"
done

# Symlink hooks
echo ""
echo "Setting up hooks..."
for file in "$SOURCE_DIR"/hooks/*; do
    [ -f "$file" ] || continue
    filename=$(basename "$file")
    create_symlink "$file" "$TARGET_DIR/hooks/$filename" "$filename"
done

# Symlink skills
echo ""
echo "Setting up skills..."
for file in "$SOURCE_DIR"/skills/*; do
    [ -f "$file" ] || continue
    filename=$(basename "$file")
    create_symlink "$file" "$TARGET_DIR/skills/$filename" "$filename"
done

# Symlink rules
echo ""
echo "Setting up rules..."
for file in "$SOURCE_DIR"/rules/*.md; do
    [ -f "$file" ] || continue
    filename=$(basename "$file")
    create_symlink "$file" "$TARGET_DIR/rules/$filename" "$filename"
done

# Configure settings.json (hook configuration)
echo ""
echo "Configuring hooks..."
configure_hooks() {
    local settings_file="$TARGET_DIR/settings.json"
    local hook_path="$TARGET_DIR/hooks/precompact-capture.sh"
    local logger_dir="$SOURCE_DIR/conversation-logger/hooks"

    local hook_config='{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "auto",
        "hooks": [
          {
            "type": "command",
            "command": "'"$hook_path"'"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "'"$logger_dir/on-assistant-turn.sh"'"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "'"$logger_dir/on-session-end.sh"'"
          }
        ]
      }
    ]
  }
}'

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY RUN] Would configure hooks in $settings_file${NC}"
        return
    fi

    if [ -f "$settings_file" ]; then
        if command -v jq &> /dev/null; then
            cp "$settings_file" "$settings_file.bak"
            jq -s '.[0] * .[1]' "$settings_file" <(echo "$hook_config") > "$settings_file.tmp"
            mv "$settings_file.tmp" "$settings_file"
            echo -e "${GREEN}  + Merged hooks into settings.json${NC}"
        else
            echo -e "${YELLOW}  ! jq not found — please manually add hook configuration${NC}"
        fi
    else
        echo "$hook_config" > "$settings_file"
        echo -e "${GREEN}  + Created settings.json${NC}"
    fi
}
configure_hooks

# Write metadata
echo ""
echo "Writing metadata..."
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY RUN] Would write: .claude-kit-source = $SOURCE_DIR${NC}"
    echo -e "${BLUE}[DRY RUN] Would write: .claude-kit-version = $VERSION${NC}"
else
    echo "$SOURCE_DIR" > "$TARGET_DIR/.claude-kit-source"
    echo "$VERSION" > "$TARGET_DIR/.claude-kit-version"
    echo -e "${GREEN}  + Source: $SOURCE_DIR${NC}"
    echo -e "${GREEN}  + Version: $VERSION${NC}"
fi

# Write hook paths config
write_hook_paths() {
    local config_file="$TARGET_DIR/.hook-paths.json"
    local hooks_dir="$SOURCE_DIR/hooks"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY RUN] Would write hook paths to $config_file${NC}"
        return
    fi

    local logger_hooks_dir="$SOURCE_DIR/conversation-logger/hooks"

    cat > "$config_file" << EOF
{
  "version": 2,
  "resolved_at": "$(date -Iseconds)",
  "source": "$SOURCE_DIR",
  "hooks": {
    "query-transcript": "$hooks_dir/query-transcript.py",
    "parse-transcript": "$hooks_dir/parse-transcript.py",
    "capture": "$hooks_dir/capture.sh",
    "precompact-capture": "$hooks_dir/precompact-capture.sh",
    "on-assistant-turn": "$logger_hooks_dir/on-assistant-turn.sh",
    "on-session-end": "$logger_hooks_dir/on-session-end.sh"
  }
}
EOF
    echo -e "${GREEN}  + Hook paths: $config_file${NC}"
}
write_hook_paths

echo ""
echo -e "${GREEN}Setup complete.${NC}"
echo ""
echo "Next steps:"
echo "  1. Restart Claude Code to pick up new commands"
echo "  2. Run 'init.sh' in each project that needs .project/"
echo ""
echo "Commands available as /_<command> (e.g., /_cycle, /_spec, /_wrapup)"
echo ""
echo "To update later: cd $SOURCE_DIR && git pull"
