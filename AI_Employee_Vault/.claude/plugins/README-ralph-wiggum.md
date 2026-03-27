# Ralph Wiggum Stop Hook Configuration

## Purpose

The Ralph Wiggum pattern keeps Qwen Code working autonomously on multi-step tasks until completion. It intercepts Qwen's attempt to exit and re-injects the prompt if the task isn't complete.

## Setup Instructions

### Option 1: Global Installation (Recommended)

Copy this plugin to your global Qwen Code plugins directory:

**Windows:**
```powershell
# Copy to global Qwen Code plugins
copy ralph-wiggum-stop-hook.ps1 $env:USERPROFILE\.qwen\plugins\
```

**macOS/Linux:**
```bash
# Copy to global Qwen Code plugins
cp ralph-wiggum-stop-hook.sh ~/.qwen/plugins/
```

### Option 2: Project-Specific Installation

The plugin is already configured in this vault at:
`.claude/plugins/ralph-wiggum-stop-hook.ps1`

When running Qwen Code from this vault directory, the plugin will auto-load.

## Usage

### Basic Usage

```bash
# Navigate to vault
cd E:\personal_ai_employee\AI_Employee_Vault

# Start Qwen with Ralph Wiggum loop
qwen "Process all files in /Needs_Action, create plans, and move completed items to /Done"
```

The stop hook will:
1. Let Qwen work on the task
2. When Qwen tries to exit, check if `/Needs_Action` is empty
3. If items remain, re-inject the prompt
4. Loop continues until all items are processed

### With Completion Promise

For tasks with a specific completion marker:

```bash
qwen "Generate the Monday Morning CEO Briefing. Output <promise>TASK_COMPLETE</promise> when done"
```

### Manual Trigger

Create a state file to trigger processing:

```bash
# Create a task file
echo "Process inbox items" > .qwen_tasks.md

# Qwen will process until file is moved to /Done
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. User gives Qwen a task                                  │
│  2. Qwen works on the task                                  │
│  3. Qwen tries to exit (outputs </task>)                    │
│  4. Stop hook intercepts the exit                           │
│  5. Check: Is task complete?                                │
│     - YES → Allow exit                                      │
│     - NO  → Block exit, re-inject prompt                    │
│  6. Qwen sees its previous output + new prompt              │
│  7. Loop continues until complete or max iterations         │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

Edit the stop hook script to customize:

- `MAX_ITERATIONS`: Maximum loop iterations (default: 10)
- `CHECK_PATHS`: Folders to check for completion
- `COMPLETION_MARKERS`: Text patterns indicating completion

## Troubleshooting

### Hook Not Triggering

Ensure the plugin file is in the correct location:
- Global: `~/.qwen/plugins/`
- Project: `./.claude/plugins/`

### Infinite Loop

If Qwen gets stuck:
1. Press `Ctrl+C` to interrupt
2. Check the task complexity - may need to break into smaller steps
3. Increase `MAX_ITERATIONS` if task legitimately needs more steps

### Task Not Completing

Review Qwen's output to understand what's blocking:
- Missing permissions?
- Unclear instructions?
- External dependency failure?

## Reference

Original Ralph Wiggum Pattern:
https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
