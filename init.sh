#!/bin/bash
# claude-kit Project Initialization
# Copies project template to .project/ in current directory
#
# Usage:
#   ./init.sh [--no-track] [--force] [--source <path>] [--dry-run]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DRY_RUN=false
NO_TRACK=false
FORCE_UPDATE=false
SOURCE_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --no-track) NO_TRACK=true; shift ;;
        --force) FORCE_UPDATE=true; shift ;;
        --source) SOURCE_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --dry-run     Show what would be done without making changes"
            echo "  --no-track    Add .project to .gitignore"
            echo "  --force       Update template files (preserves user data)"
            echo "  --source PATH Override source location"
            echo "  -h, --help    Show this help message"
            echo ""
            echo "The --force option updates templates but never touches:"
            echo "  CURRENT_WORK.md, backlog/BACKLOG.md, completed/CHANGELOG.md, learnings/index.md"
            exit 0
            ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

# Determine source directory
if [ -z "$SOURCE_DIR" ]; then
    if [ -f "$HOME/.claude/.claude-kit-source" ]; then
        SOURCE_DIR=$(cat "$HOME/.claude/.claude-kit-source")
    elif [ -f "$HOME/.claude/.agentic-pack-source" ]; then
        SOURCE_DIR=$(cat "$HOME/.claude/.agentic-pack-source")
    else
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        if [ -d "$SCRIPT_DIR/project-template" ]; then
            SOURCE_DIR="$SCRIPT_DIR"
        fi
    fi
fi

if [ -z "$SOURCE_DIR" ] || [ ! -d "$SOURCE_DIR/project-template" ]; then
    echo -e "${RED}Error: Cannot determine source location.${NC}"
    echo ""
    echo "Options:"
    echo "  1. Run setup.sh first (stores source location)"
    echo "  2. Use --source <path> to specify the claude-kit repo location"
    exit 1
fi

TEMPLATE_DIR="$SOURCE_DIR/project-template"

echo -e "${GREEN}claude-kit Project Init${NC}"
echo "======================"
[ "$DRY_RUN" = true ] && echo -e "${YELLOW}[DRY RUN MODE]${NC}"
echo ""

# Files that contain user data — NEVER overwrite
USER_DATA_FILES=(
    "CURRENT_WORK.md"
    "backlog/BACKLOG.md"
    "completed/CHANGELOG.md"
    "learnings/index.md"
)

is_user_data() {
    local file="$1"
    for protected in "${USER_DATA_FILES[@]}"; do
        [ "$file" = "$protected" ] && return 0
    done
    return 1
}

copy_file() {
    local src="$1"
    local dest="$2"
    local rel_path="$3"

    if [ -e "$dest" ]; then
        if is_user_data "$rel_path"; then
            [ "$FORCE_UPDATE" = true ] && echo -e "${YELLOW}  ! Protected: $rel_path${NC}"
            return 0
        elif [ "$FORCE_UPDATE" = true ]; then
            if [ "$DRY_RUN" = true ]; then
                echo -e "${BLUE}[DRY RUN] Would update: $rel_path${NC}"
            else
                cp "$src" "$dest"
                echo -e "${GREEN}  + Updated: $rel_path${NC}"
            fi
        fi
    else
        if [ "$DRY_RUN" = true ]; then
            echo -e "${BLUE}[DRY RUN] Would add: $rel_path${NC}"
        else
            mkdir -p "$(dirname "$dest")"
            cp "$src" "$dest"
            echo -e "${GREEN}  + $rel_path${NC}"
        fi
    fi
}

add_to_gitignore() {
    local pattern="$1"
    local gitignore=".gitignore"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY RUN] Would add '$pattern' to .gitignore${NC}"
        return
    fi

    touch "$gitignore"
    if ! grep -qxF "$pattern" "$gitignore"; then
        echo "$pattern" >> "$gitignore"
        echo -e "${GREEN}  + Added '$pattern' to .gitignore${NC}"
    fi
}

# Copy project template
echo "Setting up .project/..."

if [ -d ".project" ]; then
    if [ "$FORCE_UPDATE" = true ]; then
        echo -e "${YELLOW}  .project/ exists, updating templates...${NC}"
    else
        echo -e "${YELLOW}  .project/ exists, adding missing files...${NC}"
    fi

    while IFS= read -r -d '' src_file; do
        rel_path="${src_file#$TEMPLATE_DIR/}"
        dest_file=".project/$rel_path"
        copy_file "$src_file" "$dest_file" "$rel_path"
    done < <(find "$TEMPLATE_DIR" -type f -print0)

    # Ensure required subdirectories exist
    for dir in active backlog completed research learnings; do
        if [ ! -d ".project/$dir" ]; then
            if [ "$DRY_RUN" = true ]; then
                echo -e "${BLUE}[DRY RUN] Would create: .project/$dir/${NC}"
            else
                mkdir -p ".project/$dir"
                echo -e "${GREEN}  + Created: $dir/${NC}"
            fi
        fi
    done
else
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY RUN] Would copy project-template/ to .project/${NC}"
    else
        cp -r "$TEMPLATE_DIR" .project
        mkdir -p .project/active .project/research
        echo -e "${GREEN}  + Created .project/${NC}"
    fi
fi

# Clean up stale agentic-project-init artifacts
if [ -d ".project/memories" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would remove stale: .project/memories/${NC}"
    else
        rm -rf .project/memories
        echo -e "${YELLOW}  - Removed stale: memories/${NC}"
    fi
fi
if [ -d ".project/reports" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would remove stale: .project/reports/${NC}"
    else
        rm -rf .project/reports
        echo -e "${YELLOW}  - Removed stale: reports/${NC}"
    fi
fi
if [ -d ".project/scripts" ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would remove stale: .project/scripts/${NC}"
    else
        rm -rf .project/scripts
        echo -e "${YELLOW}  - Removed stale: scripts/${NC}"
    fi
fi

# Handle --no-track
if [ "$NO_TRACK" = true ]; then
    echo ""
    echo "Configuring no-track mode..."
    add_to_gitignore ".project"
fi

echo ""
echo -e "${GREEN}Project init complete.${NC}"
echo ""
echo "Next steps:"
echo "  1. Commit: git add .project && git commit -m 'Add project management'"
echo "  2. Commands available as /_<command> (e.g., /_cycle, /_status)"

if [ ! -f "CLAUDE.md" ]; then
    echo ""
    echo -e "${YELLOW}Tip: No CLAUDE.md found.${NC}"
    echo "Run /init in Claude Code to generate one interactively."
fi
