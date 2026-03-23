#!/bin/bash
# Ralph Wiggum Stop Hook for macOS/Linux (Bash)
#
# This script intercepts Claude Code's exit and checks if tasks are complete.
# If not, it re-injects the prompt to keep Claude working.
#
# Installation: Copy to ~/.claude/plugins/ or ./.claude/plugins/
# Usage: ./ralph-wiggum-stop-hook.sh "Your task prompt"

set -e

# Configuration
MAX_ITERATIONS=${MAX_ITERATIONS:-10}
VAULT_PATH="${VAULT_PATH:-$(pwd)}"
NEEDS_ACTION_PATH="$VAULT_PATH/Needs_Action"
DONE_PATH="$VAULT_PATH/Done"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Check if task is complete
test_task_complete() {
    local output="$1"
    
    # Check for completion markers in output
    if echo "$output" | grep -qE "(TASK_COMPLETE|DONE|COMPLETE)"; then
        echo -e "${GREEN}✓ Completion marker found${NC}"
        return 0
    fi
    
    # Check if Needs_Action folder is empty
    if [ -d "$NEEDS_ACTION_PATH" ]; then
        local file_count=$(find "$NEEDS_ACTION_PATH" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l)
        if [ "$file_count" -eq 0 ]; then
            echo -e "${GREEN}✓ Needs_Action folder is empty${NC}"
            return 0
        fi
        echo -e "${YELLOW}○ Items remaining in Needs_Action: $file_count${NC}"
    fi
    
    return 1
}

# Main Ralph loop
ralph_loop() {
    local prompt="$1"
    local iteration=0
    local last_output=""
    
    echo -e "\n${CYAN}🔄 Starting Ralph Wiggum Loop${NC}"
    echo -e "${CYAN}   Task: $prompt${NC}"
    echo -e "${CYAN}   Max Iterations: $MAX_ITERATIONS${NC}"
    echo -e "${CYAN}   Press Ctrl+C to stop${NC}\n"
    
    while [ $iteration -lt $MAX_ITERATIONS ]; do
        iteration=$((iteration + 1))
        
        echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}Iteration $iteration of $MAX_ITERATIONS${NC}"
        echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        
        # Build the prompt
        local full_prompt="$prompt"
        if [ -n "$last_output" ]; then
            full_prompt="$prompt

---
PREVIOUS OUTPUT:
$last_output

Continue working on the task. If you believe you are done, verify that all items are processed."
        fi
        
        echo -e "${YELLOW}Running Claude Code...${NC}"
        
        # Run Claude Code and capture output
        # Note: This is a simplified version - actual implementation would need
        # proper integration with claude-code CLI
        local claude_output=""
        
        # In practice, you would run:
        # claude_output=$(claude "$full_prompt" 2>&1)
        
        # Check if task is complete
        if test_task_complete "$claude_output"; then
            echo -e "\n${GREEN}✅ Task Complete!${NC}"
            break
        fi
        
        last_output="$claude_output"
    done
    
    if [ $iteration -ge $MAX_ITERATIONS ]; then
        echo -e "\n${RED}⚠️  Maximum iterations reached${NC}"
    fi
}

# Display help
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    cat << EOF
Ralph Wiggum Stop Hook

Usage: $0 [OPTIONS] "Your task prompt"

Options:
  -h, --help          Show this help message
  -i, --iterations N  Set max iterations (default: 10)
  -v, --vault PATH    Set vault path (default: current directory)

Examples:
  $0 "Process all files in /Needs_Action"
  $0 -i 20 "Generate the weekly briefing"
  $0 -v /path/to/vault "Audit last month's transactions"

EOF
    exit 0
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        -v|--vault)
            VAULT_PATH="$2"
            NEEDS_ACTION_PATH="$VAULT_PATH/Needs_Action"
            shift 2
            ;;
        *)
            TASK_PROMPT="$1"
            shift
            ;;
    esac
done

if [ -z "$TASK_PROMPT" ]; then
    echo -e "${RED}Error: Task prompt is required${NC}"
    echo "Usage: $0 \"Your task prompt\""
    exit 1
fi

# Run the Ralph loop
ralph_loop "$TASK_PROMPT"
