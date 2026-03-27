# Personal AI Employee Project

## Project Overview

This is a **Digital FTE (Full-Time Equivalent)** project — an autonomous AI agent system that manages personal and business affairs 24/7. Built around **Claude Code** as the reasoning engine and **Obsidian** as the knowledge dashboard, it implements a local-first, agent-driven automation architecture.

**Core Concept:** Transform AI from a reactive chatbot into a proactive "employee" that:
- Monitors communications (Gmail, WhatsApp, etc.) via lightweight "Watcher" scripts
- Reasons about tasks and creates action plans using Claude Code
- Executes actions through MCP (Model Context Protocol) servers
- Maintains human-in-the-loop approval for sensitive operations

**Tagline:** *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT (Memory/GUI)              │
│  Dashboard.md | Company_Handbook.md | /Inbox | /Needs_Action│
└─────────────────────────────────────────────────────────────┘
                            ↕ reads/writes
┌─────────────────────────────────────────────────────────────┐
│                  CLAUDE CODE (Reasoning Engine)             │
│         Ralph Wiggum Loop for multi-step persistence        │
└─────────────────────────────────────────────────────────────┘
                    ↕ triggers              ↕ executes via MCP
┌──────────────────────┐          ┌───────────────────────────┐
│   WATCHERS (Senses)  │          │   MCP SERVERS (Hands)     │
│  - Gmail Watcher     │          │  - Email MCP              │
│  - WhatsApp Watcher  │          │  - Browser/Playwright MCP │
│  - Filesystem Watcher│          │  - Calendar MCP           │
│  - Finance Watcher   │          │  - Odoo Accounting MCP    │
└──────────────────────┘          └───────────────────────────┘
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **The Brain** | Reasoning and planning | Claude Code |
| **The Memory** | Long-term storage + GUI | Obsidian (Markdown vault) |
| **The Senses** | Continuous monitoring | Python Watcher scripts |
| **The Hands** | External system interaction | MCP Servers |
| **Persistence** | Multi-step task completion | Ralph Wiggum Stop Hook |

## Directory Structure

```
personal_ai_employee/
├── AI_Employee_Vault/                   # Obsidian vault (Bronze Tier)
│   ├── Dashboard.md                     # Real-time status dashboard
│   ├── Company_Handbook.md              # Rules of engagement
│   ├── Business_Goals.md                # Objectives and metrics
│   ├── Inbox/                           # Raw incoming files
│   ├── Needs_Action/                    # Items requiring processing
│   ├── Done/                            # Completed items
│   ├── Plans/                           # Task plans
│   ├── Pending_Approval/                # Awaiting human decision
│   ├── Approved/                        # Ready for execution
│   ├── Rejected/                        # Declined items
│   ├── Logs/                            # System logs
│   ├── Briefings/                       # CEO briefings
│   └── .claude/plugins/                 # Ralph Wiggum stop hook
├── src/                                 # Python source files
│   ├── base_watcher.py                  # Base class for watchers
│   ├── filesystem_watcher.py            # Bronze tier watcher
│   └── orchestrator.py                  # Master orchestration
├── .agents/
│   └── skills/
│       └── browsing-with-playwright/    # Browser automation skill
│           ├── SKILL.md                 # Skill documentation
│           ├── references/
│           │   └── playwright-tools.md  # MCP tool reference
│           └── scripts/
│               ├── mcp-client.py        # Universal MCP client (HTTP/stdio)
│               ├── start-server.sh      # Start Playwright MCP server
│               ├── stop-server.sh       # Stop Playwright MCP server
│               └── verify.py            # Server health check
├── README.md                            # Setup guide
├── requirements.txt                     # Python dependencies
├── skills-lock.json                     # Installed skills registry
└── QWEN.md                              # This file
```

## Building and Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Claude Code | Active subscription | Primary reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Python | 3.13+ | Watcher scripts & orchestration |
| Node.js | v24+ LTS | MCP servers |
| GitHub Desktop | Latest | Version control |

### Bronze Tier - Quick Start

**1. Open Vault in Obsidian:**
- Open `AI_Employee_Vault/` as a vault in Obsidian
- Review `Dashboard.md`, `Company_Handbook.md`, `Business_Goals.md`

**2. Start Filesystem Watcher:**
```bash
cd E:\personal_ai_employee
python src/filesystem_watcher.py AI_Employee_Vault
```

**3. Start Orchestrator (in second terminal):**
```bash
cd E:\personal_ai_employee
python src/orchestrator.py AI_Employee_Vault
```

**4. Test the System:**
- Drop a file into `~/AI_Employee_Drop` (or custom folder)
- Watcher creates action file in `/Needs_Action`
- Orchestrator processes and creates plan

### Playwright MCP Skill

The project includes a browser automation skill for web interactions.

**Start the MCP Server:**
```bash
bash .agents/skills/browsing-with-playwright/scripts/start-server.sh
# Or manually:
npx @playwright/mcp@latest --port 8808 --shared-browser-context &
```

**Verify Server:**
```bash
python .agents/skills/browsing-with-playwright/scripts/verify.py
```

**Stop the Server:**
```bash
bash .agents/skills/browsing-with-playwright/scripts/stop-server.sh
```

**Call MCP Tools:**
```bash
# List available tools
python .agents/skills/browsing-with-playwright/scripts/mcp-client.py list \
  -u http://localhost:8808

# Navigate to a URL
python .agents/skills/browsing-with-playwright/scripts/mcp-client.py call \
  -u http://localhost:8808 -t browser_navigate \
  -p '{"url": "https://example.com"}'

# Take a page snapshot
python .agents/skills/browsing-with-playwright/scripts/mcp-client.py call \
  -u http://localhost:8808 -t browser_snapshot -p '{}'
```

### Watcher Scripts (To Implement)

Watchers are Python scripts that monitor external systems and create action files in the Obsidian vault:

```python
# Example: Gmail Watcher pattern
from base_watcher import BaseWatcher

class GmailWatcher(BaseWatcher):
    def check_for_updates(self) -> list:
        # Check for new unread emails
        pass
    
    def create_action_file(self, email) -> Path:
        # Create .md file in /Needs_Action folder
        pass
```

**Recommended Watchers:**
- `gmail_watcher.py` - Monitor Gmail for important unread messages
- `whatsapp_watcher.py` - Monitor WhatsApp Web for urgent keywords
- `filesystem_watcher.py` - Watch drop folders for new files
- `finance_watcher.py` - Track bank transactions

### Ralph Wiggum Loop (Persistence Pattern)

Use the Ralph Wiggum Stop hook to keep Claude working on multi-step tasks until completion:

```bash
# Start a Ralph loop
/ralph-loop "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

**How it works:**
1. Orchestrator creates state file with prompt
2. Claude works on task
3. Claude tries to exit
4. Stop hook checks: Is task file in /Done?
5. YES → Allow exit; NO → Block exit, re-inject prompt (loop continues)

## Development Conventions

### Obsidian Vault Structure

```
Vault/
├── Dashboard.md              # Real-time summary
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Q1/Q2 objectives
├── Inbox/                    # Raw incoming items
├── Needs_Action/             # Items requiring processing
├── In_Progress/<agent>/      # Claimed by specific agent
├── Pending_Approval/         # Awaiting human approval
├── Approved/                 # Ready for execution
├── Done/                     # Completed items
└── Briefings/                # CEO briefings (generated)
```

### Human-in-the-Loop Pattern

For sensitive actions (payments, sending messages), Claude writes an approval request file instead of acting directly:

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
status: pending
---

## Payment Details
- Amount: $500.00
- To: Client A

## To Approve
Move this file to /Approved folder.
```

### MCP Server Configuration

Configure MCP servers in Claude Code settings (`~/.config/claude-code/mcp.json`):

```json
{
  "servers": [
    {
      "name": "browser",
      "command": "npx",
      "args": ["@playwright/mcp"],
      "env": { "HEADLESS": "true" }
    },
    {
      "name": "email",
      "command": "node",
      "args": ["/path/to/email-mcp/index.js"]
    }
  ]
}
```

## Achievement Tiers

| Tier | Description | Estimated Time |
|------|-------------|----------------|
| **Bronze** | Foundation: Obsidian vault, one Watcher, basic Claude integration | 8-12 hours |
| **Silver** | Functional: Multiple Watchers, MCP servers, HITL workflow | 20-30 hours |
| **Gold** | Autonomous: Full integration, Odoo accounting, weekly audits | 40+ hours |
| **Platinum** | Production: Cloud deployment, domain specialization, A2A sync | 60+ hours |

## Key Resources

- [Playwright MCP Tools Reference](.agents/skills/browsing-with-playwright/references/playwright-tools.md)
- [Skill Documentation](.agents/skills/browsing-with-playwright/SKILL.md)
- [Hackathon Blueprint](Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md)
- [Ralph Wiggum Pattern](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Playwright MCP not responding | Run `verify.py`; restart with `stop-server.sh && start-server.sh` |
| Element click fails | Run `browser_snapshot` first to get current element refs |
| Watcher not triggering | Check Python script logs; verify API credentials |
| Claude exits prematurely | Enable Ralph Wiggum Stop hook for persistence |
