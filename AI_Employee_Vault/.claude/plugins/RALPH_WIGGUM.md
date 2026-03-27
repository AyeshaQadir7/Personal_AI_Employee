# Ralph Wiggum Stop Hook - Persistence Pattern

## Overview

The Ralph Wiggum pattern keeps Claude Code working on multi-step tasks until completion. It intercepts Claude's exit attempt and re-injects the prompt if the task isn't complete.

## How It Works

```
┌─────────────────┐
│ 1. Start Ralph  │
│    Loop         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Claude works │
│    on task      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Claude tries │
│    to exit      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     NO      ┌─────────────────┐
│ 4. Stop hook    │────────────▶│ 5. Block exit,  │
│    checks: Is   │  Task Done? │    re-inject    │
│    task in      │             │    prompt       │
│    /Done?       │             │    (loop)       │
└────────┬────────┘             └────────┬────────┘
         │ YES                           │
         │                               │
         ▼                               │
┌─────────────────┐                     │
│ 6. Allow exit   │◀────────────────────┘
│    (complete)   │
└─────────────────┘
```

## Usage

### Basic Usage

```bash
# Start a Ralph loop
claude
/ralph-loop "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

### With File Movement Detection (Advanced)

For more reliable completion detection, use file movement:

```bash
# Create state file
echo "Process invoice files in /Needs_Action" > .claude/state_current_task.txt

# Start Claude with Ralph
claude --prompt-file .claude/ralph_prompt.md

# Ralph hook checks:
# 1. Is state file in /Done?
# 2. If YES → Allow exit
# 3. If NO → Re-inject prompt
```

## Configuration

### Prompt File Format

Create `.claude/ralph_prompt.md`:

```markdown
# Task: Process Invoice Files

## Objective
Process all invoice files in /Needs_Action folder:
1. Extract invoice details (amount, vendor, due date)
2. Log in accounting tracker
3. Create payment schedules
4. Move processed files to /Done

## Completion Criteria
Task is complete when:
- All .md files moved from /Needs_Action to /Done
- OR approval requests created in /Pending_Approval for items needing review

## Rules
- Follow Company_Handbook.md for payment thresholds
- Flag invoices >$100 for approval
- Log all actions in /Logs

## Current State
Check /Needs_Action folder for remaining files.
```

### State File Format

Create `.claude/state_current_task.txt`:

```
TASK: Process Invoice Files
CREATED: 2026-01-07T10:30:00Z
MAX_ITERATIONS: 10
CURRENT_ITERATION: 0
COMPLETION_CHECK: Move all files from /Needs_Action to /Done
```

## Integration with Orchestrator

The Orchestrator can create Ralph loop state files:

```python
# In orchestrator.py
def start_ralph_loop(self, task_description: str):
    """Start a Ralph Wiggum loop for multi-step task."""
    state_file = self.vault_path / '.claude' / 'state_current_task.txt'
    
    content = f"""TASK: {task_description}
CREATED: {datetime.now().isoformat()}
MAX_ITERATIONS: 10
CURRENT_ITERATION: 0
COMPLETION_CHECK: Check /Done folder for completed items
"""
    state_file.write_text(content)
    
    # Create prompt file
    prompt_file = self.vault_path / '.claude' / 'ralph_prompt.md'
    prompt_file.write_text(f"""
# Task: {task_description}

Please complete this task. When done, move all processed files to /Done.

Current state: {state_file}
""")
    
    self.logger.info(f"Ralph loop state created: {state_file}")
```

## Completion Strategies

### 1. Promise-Based (Simple)

Claude outputs a specific string when done:

```bash
/ralph-loop "Process emails" \
  --completion-promise "TASK_COMPLETE"
```

Claude must output: `<promise>TASK_COMPLETE</promise>`

### 2. File Movement (Advanced - Recommended)

Stop hook detects when task file moves to /Done:

```python
# ralph_stop_hook.py
import sys
from pathlib import Path

def check_completion(state_file: Path) -> bool:
    """Check if task is complete."""
    if not state_file.exists():
        return False
    
    content = state_file.read_text()
    
    # Parse completion check
    for line in content.split('\n'):
        if line.startswith('COMPLETION_CHECK:'):
            check = line.split(':', 1)[1].strip()
            return evaluate_check(check)
    
    return False

def evaluate_check(check: str) -> bool:
    """Evaluate completion check."""
    # Example: "Check /Done folder for completed items"
    if '/Done' in check:
        done_folder = Path('AI_Employee_Vault/Done')
        return done_folder.exists() and len(list(done_folder.glob('*.md'))) > 0
    
    return False

if __name__ == "__main__":
    state_file = Path('AI_Employee_Vault/.claude/state_current_task.txt')
    
    if check_completion(state_file):
        print("TASK_COMPLETE")
        sys.exit(0)  # Allow exit
    else:
        print("TASK_INCOMPLETE")
        sys.exit(1)  # Block exit, re-inject prompt
```

## Example: Multi-Step Email Processing

```bash
# Start Ralph loop for email processing
claude
/ralph-loop "Process all unread emails from Gmail" \
  --max-iterations 5

# Claude:
# 1. Reads /Needs_Action/EMAIL_*.md files
# 2. Creates drafts for responses
# 3. Creates approval requests for sensitive emails
# 4. Moves processed files to /Done

# When Claude tries to exit:
# Ralph hook checks: Are all EMAIL_*.md files in /Done?
# YES → Allow exit
# NO → Re-inject: "Continue processing remaining emails"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Loop never ends | Check completion criteria is achievable |
| Exits too early | Use file movement detection, not promise |
| Max iterations hit | Increase --max-iterations or simplify task |
| Prompt not re-injected | Check Ralph hook is properly configured |

## Best Practices

1. **Clear completion criteria** - Define exactly what "done" looks like
2. **Reasonable max iterations** - Prevent infinite loops (5-10 typical)
3. **Log each iteration** - Track progress in state file
4. **Graceful degradation** - Allow partial completion with approval requests
5. **Test with simple tasks first** - Verify loop works before complex tasks

## Reference

- [Official Ralph Wiggum Pattern](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
- [Claude Code Plugins](https://claude.com/docs/claude-code/plugins)
