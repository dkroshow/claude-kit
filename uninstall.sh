#!/bin/bash
# claude-kit Uninstall
# Removes claude-kit from ~/.claude/ (--global) or .project/ from current dir (--project)
#
# Usage:
#   ./uninstall.sh --global    Remove global installation from ~/.claude/
#   ./uninstall.sh --project   Remove .project/ from current directory
#   ./uninstall.sh --all       Both

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DO_GLOBAL=false
DO_PROJECT=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --global) DO_GLOBAL=true; shift ;;
        --project) DO_PROJECT=true; shift ;;
        --all) DO_GLOBAL=true; DO_PROJECT=true; shift ;;
        --force) FORCE=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--global] [--project] [--all] [--force]"
            echo ""
            echo "Options:"
            echo "  --global   Remove global installation from ~/.claude/"
            echo "  --project  Remove .project/ from current directory"
            echo "  --all      Both global and project"
            echo "  --force    Skip confirmation prompts"
            exit 0
            ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

if [ "$DO_GLOBAL" = false ] && [ "$DO_PROJECT" = false ]; then
    echo -e "${RED}Error: Specify --global, --project, or --all${NC}"
    echo "Run with --help for usage."
    exit 1
fi

echo -e "${GREEN}claude-kit Uninstall${NC}"
echo "==================="
echo ""

# --- Global uninstall ---
if [ "$DO_GLOBAL" = true ]; then
    TARGET_DIR="$HOME/.claude"
    SOURCE_FILE="$TARGET_DIR/.claude-kit-source"

    if [ ! -f "$SOURCE_FILE" ]; then
        echo -e "${YELLOW}No claude-kit global installation found.${NC}"
    else
        SOURCE_DIR=$(cat "$SOURCE_FILE")
        REMOVED=0

        echo "Removing global installation..."

        # Remove symlinks pointing to our source
        for subdir in commands agents hooks skills rules; do
            [ -d "$TARGET_DIR/$subdir" ] || continue
            for file in "$TARGET_DIR/$subdir"/*; do
                [ -L "$file" ] || continue
                target=$(readlink "$file")
                if [[ "$target" == "$SOURCE_DIR"* ]]; then
                    rm "$file"
                    echo -e "${GREEN}  - $subdir/$(basename "$file")${NC}"
                    ((REMOVED++)) || true
                fi
            done
        done

        # Clean hook config from settings.json
        settings_file="$TARGET_DIR/settings.json"
        if [ -f "$settings_file" ] && command -v jq &> /dev/null; then
            if jq -e '.hooks.PreCompact' "$settings_file" > /dev/null 2>&1; then
                cp "$settings_file" "$settings_file.bak"
                jq 'if .hooks.PreCompact then .hooks.PreCompact = [.hooks.PreCompact[] | select(.hooks | all(.command | contains("/.claude/hooks/") | not))] else . end | if .hooks.PreCompact == [] then del(.hooks.PreCompact) else . end | if .hooks == {} then del(.hooks) else . end' "$settings_file" > "$settings_file.tmp"
                mv "$settings_file.tmp" "$settings_file"
                echo -e "${GREEN}  - Cleaned hook config${NC}"
            fi
        fi

        # Remove metadata
        for file in .claude-kit-source .claude-kit-version .hook-paths.json; do
            if [ -f "$TARGET_DIR/$file" ]; then
                rm "$TARGET_DIR/$file"
                echo -e "${GREEN}  - $file${NC}"
                ((REMOVED++)) || true
            fi
        done

        echo ""
        echo -e "${GREEN}Global uninstall complete. Removed $REMOVED items.${NC}"
    fi
fi

# --- Project uninstall ---
if [ "$DO_PROJECT" = true ]; then
    if [ ! -d ".project" ]; then
        echo -e "${YELLOW}No .project/ directory found in current directory.${NC}"
    else
        if [ "$FORCE" != true ]; then
            echo "This will remove .project/ and all contents."
            read -p "Are you sure? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Cancelled."
                exit 0
            fi
        fi

        rm -rf .project
        echo -e "${GREEN}  - Removed .project/${NC}"

        # Clean .gitignore
        if [ -f ".gitignore" ] && grep -qxF ".project" .gitignore; then
            grep -vxF ".project" .gitignore > .gitignore.tmp || true
            mv .gitignore.tmp .gitignore
            echo -e "${GREEN}  - Removed .project from .gitignore${NC}"
        fi

        echo ""
        echo -e "${GREEN}Project uninstall complete.${NC}"
    fi
fi
