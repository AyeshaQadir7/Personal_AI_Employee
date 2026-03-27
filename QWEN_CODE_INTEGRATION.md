# Qwen Code Integration Guide for AI Employee

> **Using Qwen Code as the Brain instead of Claude Code**

This guide explains how to use Qwen Code with your AI Employee for Silver Tier functionality.

## Architecture Adaptation

The hackathon document references Claude Code, but we've adapted the architecture for **Qwen Code**:

| Original (Claude Code) | Adapted (Qwen Code) |
|------------------------|---------------------|
| Claude Code reasoning | Qwen Code reasoning |
| `/ralph-loop` command | Qwen Code with persistence prompt |
| Claude MCP config | Qwen MCP config (same format) |
| Claude skills | Qwen Code agent skills |

## Setup Qwen Code

### 1. Install Qwen Code

```bash
# Install via npm (if available)
npm install -g @anthropic/qwen-code

# Or use the web interface at https://qwen.ai/
```

### 2. Configure MCP Servers

Create or edit `~/.qwen/mcp.json` (or use the project-level config):

```json
{
  "servers": [
    {
      "name": "email",
      "command": "python",
      "args": ["E:\\personal_ai_employee\\.agents\\skills\\email-mcp-server\\scripts\\email_mcp_server.py"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "E:\\personal_ai_employee\\credentials.json"
      }
    },
    {
      "name": "browser",
      "command": "npx",
      "args": ["@playwright/mcp"],
      "env": {
        "HEADLESS": "true"
      }
    },
    {
      "name": "linkedin",
      "command": "python",
      "args": ["E:\\personal_ai_employee\\.agents\\skills\\linkedin-mcp-server\\scripts\\linkedin_mcp_server.py"]
    }
  ]
}
```

### 3. Verify Qwen Code Works

```bash
# Test Qwen Code
qwen --version

# Or interactive mode
qwen
```

## Running the AI Employee with Qwen Code

### Step 1: Start Watchers

Open separate terminals for each watcher:

```bash
# Terminal 1: Gmail Watcher
cd E:\personal_ai_employee
python src/gmail_watcher.py AI_Employee_Vault --interval 120

# Terminal 2: LinkedIn Watcher
cd E:\personal_ai_employee
python src/linkedin_watcher.py AI_Employee_Vault --interval 300

# Terminal 3: Filesystem Watcher (already running from Bronze)
cd E:\personal_ai_employee
python src/filesystem_watcher.py AI_Employee_Vault --interval 5
```

### Step 2: Start Orchestrator

```bash
# Terminal 4: Orchestrator
cd E:\personal_ai_employee
python src/orchestrator.py AI_Employee_Vault --qwen
```

### Step 3: Process with Qwen Code

When action files appear in `/Needs_Action`, trigger Qwen Code:

```bash
# Manual processing
cd E:\personal_ai_employee\AI_Employee_Vault
qwen "Process all files in Needs_Action folder. Follow Company_Handbook.md rules."

# Or with prompt file
qwen --prompt-file .qwen_prompt.md
```

## Persistence Pattern (Ralph Wiggum Alternative)

Since Qwen Code may not have the exact `/ralph-loop` command, use this pattern:

### Option 1: Loop Script

Create `qwen_loop.bat` (Windows) or `qwen_loop.sh` (Linux/Mac):

```batch
@echo off
REM qwen_loop.bat - Persistence loop for Qwen Code
set VAULT=AI_Employee_Vault
set MAX_ITERATIONS=10
set ITERATION=0

:loop
if %ITERATION% GEQ %MAX_ITERATIONS% (
    echo Max iterations reached
    exit /b 1
)

echo Iteration %ITERATION% of %MAX_ITERATIONS%
qwen "Process all files in %VAULT%/Needs_Action. Move completed to Done."

REM Check if any files remain in Needs_Action
dir %VAULT%\Needs_Action\*.md /b > temp.txt
for %%a in (temp.txt) do set SIZE=%%~za
if %SIZE% GTR 0 (
    set /a ITERATION+=1
    goto loop
)

echo All tasks completed!
```

### Option 2: Orchestrator State File

The orchestrator creates a state file that Qwen Code monitors:

```bash
# Create state file
echo "Process inbox items" > AI_Employee_Vault/.state_current_task.txt

# Run Qwen Code
qwen "Monitor .state_current_task.txt. When task is complete, write TASK_COMPLETE"
```

## Processing Workflow

### 1. Gmail Email Processing

```
Gmail (new email arrives)
  ↓
Gmail Watcher (polls every 2 min)
  ↓
Creates: /Needs_Action/EMAIL_Invoice_Request_2026-03-23.md
  ↓
Orchestrator detects new file
  ↓
Moves to: /In_Progress/
  ↓
Creates: /Plans/PLAN_invoice_request.md
  ↓
Triggers Qwen Code
  ↓
Qwen Code reads email, Company_Handbook.md
  ↓
Creates approval request (if payment >$100)
  ↓
/Pending_Approval/PAYMENT_Client_A.md
  ↓
Human reviews and moves to /Approved
  ↓
Email MCP sends reply
  ↓
Moves to /Done
```

### 2. LinkedIn Opportunity Processing

```
LinkedIn (new business opportunity)
  ↓
LinkedIn Watcher (polls every 5 min)
  ↓
Creates: /Needs_Action/LINKEDIN_BUSINESS_OPPORTUNITY_2026-03-23.md
  ↓
Orchestrator detects
  ↓
Qwen Code processes
  ↓
Drafts response
  ↓
/Pending_Approval/LINKEDIN_RESPONSE_Client_B.md
  ↓
Human approves
  ↓
LinkedIn MCP sends message
  ↓
/Done
```

## Qwen Code Prompts

### Daily Processing Prompt

```markdown
# AI Employee Daily Processing

## Context
You are the AI Employee's reasoning engine. Process all pending actions
according to the Company_Handbook.md rules.

## Current Tasks
Check these folders:
- /Needs_Action - New items requiring processing
- /In_Progress - Items you're currently working on
- /Pending_Approval - Items awaiting human approval

## Instructions
1. Read each file in /Needs_Action completely
2. Determine the type of request (email, invoice, opportunity)
3. Create/update plan files in /Plans
4. Execute actions within your capabilities
5. For sensitive actions (payments, sends, posts):
   - Create approval file in /Pending_Approval
   - DO NOT execute without approval
6. When complete, move processed files to /Done

## Business Context
- Review /Business_Goals.md for current objectives
- Follow /Company_Handbook.md for rules
- Log all actions in /Logs

## Output
Update Dashboard.md with:
- Items processed
- Pending approvals
- Business metrics (revenue, response times)
```

### Weekly Audit Prompt

```markdown
# Weekly CEO Briefing

## Task
Generate a comprehensive weekly business audit and CEO briefing.

## Data Sources
1. /Business_Goals.md - Q1/Q2 objectives
2. /Done folder - Completed tasks this week
3. /Accounting folder - Financial transactions
4. /Logs - System activity logs

## Generate Briefing

Create: /Briefings/YYYY-MM-DD_Weekly_Briefing.md

Include:
### Revenue Summary
- Total revenue this week
- Month-to-date progress
- Trend analysis

### Completed Work
- Projects delivered
- Invoices sent/paid
- Client communications

### Bottlenecks
- Tasks that took longer than expected
- Pending approvals blocking progress
- Resource constraints

### Proactive Suggestions
- Subscription audit (flag unused services)
- Process improvements
- Growth opportunities

### Next Week Priorities
- Upcoming deadlines
- Scheduled deliverables
- Follow-ups needed

## Tone
Professional, data-driven, actionable insights.
```

## Troubleshooting

### Qwen Code Not Processing Files

| Issue | Solution |
|-------|----------|
| Files stuck in /Needs_Action | Manually trigger Qwen Code with prompt |
| Qwen exits too quickly | Use persistence loop script |
| Approval files not created | Check Company_Handbook.md rules |

### Watcher Issues

| Issue | Solution |
|-------|----------|
| Gmail Watcher not authenticating | Delete token.json and re-run |
| LinkedIn Watcher login fails | Run with --login flag manually |
| High CPU usage | Increase check intervals |

### MCP Server Issues

| Issue | Solution |
|-------|----------|
| Email MCP not connecting | Verify credentials.json path |
| LinkedIn MCP session expired | Re-authenticate with --login |
| Browser MCP timeout | Increase timeout or reduce headless |

## Best Practices

1. **Start watchers first** - Let them collect for 5-10 min before processing
2. **Batch process** - Run Qwen Code every 30-60 min, not continuously
3. **Review approvals daily** - Check /Pending_Approval every morning
4. **Monitor logs** - Review /Logs weekly for patterns
5. **Tune intervals** - Adjust watcher frequency based on volume

## Migration from Claude Code

If you were following the original hackathon guide:

| Claude Code Feature | Qwen Code Equivalent |
|---------------------|----------------------|
| `claude` command | `qwen` command |
| `/ralph-loop` | Custom loop script |
| `~/.config/claude-code/mcp.json` | `~/.qwen/mcp.json` or project config |
| Claude skills | Qwen Code agent skills |

The architecture remains the same - only the reasoning engine changes.

## Next Steps

After mastering Silver Tier:

1. **Gold Tier**: Add Odoo accounting integration
2. **Platinum Tier**: Deploy to cloud with 24/7 operation
3. **Custom MCP Servers**: Build domain-specific integrations

---

*For detailed skill documentation, see individual SKILL.md files in `.agents/skills/`*
