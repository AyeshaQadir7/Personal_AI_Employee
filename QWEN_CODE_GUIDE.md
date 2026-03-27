# AI Employee with Qwen Code - Silver Tier Guide

> **Note:** This project uses **Qwen Code** as the reasoning engine instead of Claude Code. All architecture remains the same - only the AI brain changes.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT (Memory/GUI)              │
│  Dashboard.md | Company_Handbook.md | /Inbox | /Needs_Action│
└─────────────────────────────────────────────────────────────┘
                            ↕ reads/writes
┌─────────────────────────────────────────────────────────────┐
│                  QWEN CODE (Reasoning Engine)               │
│         Ralph Wiggum Loop for multi-step persistence        │
└─────────────────────────────────────────────────────────────┘
                    ↕ triggers              ↕ executes via MCP
┌──────────────────────┐          ┌───────────────────────────┐
│   WATCHERS (Senses)  │          │   MCP SERVERS (Hands)     │
│  - Gmail Watcher     │          │  - Email MCP              │
│  - LinkedIn Watcher  │          │  - Browser/Playwright MCP │
│  - Filesystem Watcher│          │  - LinkedIn MCP           │
└──────────────────────┘          └───────────────────────────┘
```

---

## Key Differences from Claude Code Version

| Component | Claude Code Version | Qwen Code Version |
|-----------|--------------------|-------------------|
| **AI Brain** | `claude` command | `qwen` command |
| **MCP Config** | `~/.config/claude-code/mcp.json` | Use project `mcp.json` |
| **Ralph Wiggum** | Built-in plugin | Manual implementation |
| **Skills** | Claude Agent Skills | Qwen Skills (same pattern) |

---

## Quick Start

### 1. Start Watchers

```bash
# Terminal 1: Gmail Watcher
python src/gmail_watcher.py AI_Employee_Vault --interval 120

# Terminal 2: LinkedIn Watcher  
python src/linkedin_watcher.py AI_Employee_Vault --interval 300 --no-headless

# Terminal 3: Orchestrator
python src/orchestrator.py AI_Employee_Vault
```

### 2. Process with Qwen Code

```bash
# Terminal 4: Qwen Code
cd AI_Employee_Vault
qwen

# In Qwen session:
"Process all files in /Needs_Action folder"
```

---

## Silver Tier Components

### Watchers (Senses)

| Watcher | Purpose | Command |
|---------|---------|---------|
| **Gmail Watcher** | Monitor unread emails | `python src/gmail_watcher.py AI_Employee_Vault` |
| **LinkedIn Watcher** | Detect business opportunities | `python src/linkedin_watcher.py AI_Employee_Vault` |
| **Filesystem Watcher** | Watch Inbox folder | `python src/filesystem_watcher.py AI_Employee_Vault` |

### MCP Servers (Hands)

| Server | Purpose | Config |
|--------|---------|--------|
| **Email MCP** | Send emails via Gmail | See `mcp.json` |
| **Browser MCP** | Web automation | Playwright |
| **LinkedIn MCP** | Post to LinkedIn | See `mcp.json` |

---

## Gmail Watcher Setup

### Prerequisites

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Credentials

Your `credentials.json` is already in the root directory. This contains:
- **Client ID:** `35994880723-t3md8r97llkvloqfid2u1k953s2f87ur.apps.googleusercontent.com`
- **Project:** `digital-ai-employee-491119`

### First Run

```bash
python src/gmail_watcher.py AI_Employee_Vault
```

This will:
1. Open browser for OAuth2 consent
2. Create `token.json` (saved for future runs)
3. Start monitoring Gmail

### What It Does

- Polls Gmail every 120 seconds
- Fetches unread emails
- Creates action files in `/Needs_Action`
- Tracks processed emails (no duplicates)

### Action File Format

```markdown
---
type: email
from: client@example.com
subject: Invoice Request
priority: high
status: pending
---

# Email: Invoice Request

## Sender Information
- **From:** client@example.com
- **Priority:** HIGH

## Email Content
Hi, can you send the invoice for January?

## Suggested Actions
- [ ] Extract invoice details
- [ ] Log in accounting tracker
- [ ] Generate invoice
```

---

## LinkedIn Watcher Setup

### Prerequisites

```bash
pip install playwright
playwright install chromium
```

### First Run

```bash
python src/linkedin_watcher.py AI_Employee_Vault --login --no-headless
```

This will:
1. Open browser to LinkedIn
2. You login manually
3. Session saved to `~/.linkedin_session/`

### What It Detects

- Connection requests with business keywords
- Messages about opportunities ("hiring", "freelance", "project")
- Posts mentioning "looking for", "need help"

### Action File Format

```markdown
---
type: linkedin_message
activity_type: business_message
priority: high
status: pending
---

# LinkedIn Business Message

## Content
Hi, I'm looking for a developer to help with...

## Suggested Actions
- [ ] Review opportunity
- [ ] Research sender
- [ ] Draft response
```

---

## Qwen Code Integration

### Basic Usage

```bash
cd AI_Employee_Vault
qwen

# Prompt examples:
"Process all files in /Needs_Action"
"Create a plan for responding to these emails"
"Review Company_Handbook.md and process pending approvals"
```

### Ralph Wiggum Loop (Multi-Step Tasks)

For complex tasks that require multiple steps:

```bash
qwen

# Start loop
/ralph-loop "Process all emails, create response drafts, move completed to /Done" \
  --max-iterations 5
```

**How it works:**
1. Qwen processes files
2. Tries to exit
3. Loop checks: Are all files in /Done?
4. NO → Re-inject prompt (continue)
5. YES → Allow exit

### Creating Plans

Qwen Code creates `Plan.md` files in `/Plans/`:

```markdown
---
created: 2026-01-07T10:30:00Z
status: pending
action_file: EMAIL_Invoice_Request.md
---

# Plan: Respond to Invoice Request

## Objective
Generate and send invoice for January services

## Steps
- [x] Identify client details
- [x] Calculate amount ($1,500/month)
- [ ] Generate invoice PDF
- [ ] Send email (requires approval)
- [ ] Log transaction
```

---

## Human-in-the-Loop (HITL)

For sensitive actions (sending emails, payments, posts):

### 1. Qwen Creates Approval Request

```markdown
---
type: approval_request
action: send_email
to: client@example.com
subject: Invoice #123
created: 2026-01-07T10:30:00Z
status: pending
---

## Email Details
- **To:** client@example.com
- **Subject:** Invoice #123

## To Approve
Move to /Approved folder.
```

### 2. Human Reviews

- Move to `/Approved` → Execute action
- Move to `/Rejected` → Decline action

### 3. Orchestrator Executes

When file appears in `/Approved`:
- Email MCP sends the email
- File moved to `/Done`
- Action logged

---

## Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Q1 2026 objectives
├── Inbox/                    # Raw incoming files
├── Needs_Action/             # Items requiring processing
│   ├── EMAIL_*.md           # From Gmail Watcher
│   ├── LINKEDIN_*.md        # From LinkedIn Watcher
│   └── FILE_*.md            # From Filesystem Watcher
├── In_Progress/              # Currently being processed
├── Plans/                    # Task plans
├── Pending_Approval/         # Awaiting human decision
├── Approved/                 # Ready for execution
├── Rejected/                 # Declined items
├── Done/                     # Completed items
├── Briefings/                # CEO briefings
└── Logs/                     # System audit trail
```

---

## Scheduled Tasks

### Daily Briefing (8:00 AM)

Generates morning summary in `/Briefings/`:

```markdown
# Daily Briefing - 2026-01-07

## Yesterday's Summary
- Emails processed: 12
- LinkedIn opportunities: 2
- Tasks completed: 5

## Today's Priorities
1. Project Alpha deadline
2. Client B follow-up

## Pending Approvals
- Payment: Client A invoice ($500)
```

### Weekly Audit (Sunday 10:00 PM)

```bash
python src/orchestrator.py AI_Employee_Vault --scheduled-task weekly_audit
```

Generates CEO briefing with:
- Revenue summary
- Completed tasks
- Bottlenecks identified
- Proactive suggestions

---

## Troubleshooting

### Gmail Watcher

| Issue | Solution |
|-------|----------|
| `credentials.json not found` | File is at `E:\personal_ai_employee\credentials.json` |
| `token.json expired` | Delete and re-run authentication |
| No emails detected | Ensure unread emails exist |

### LinkedIn Watcher

| Issue | Solution |
|-------|----------|
| Login required | Run with `--login --no-headless` |
| Session not saving | Check `~/.linkedin_session/` permissions |
| No activities | Passive monitoring - wait for real activity |

### Qwen Code

| Issue | Solution |
|-------|----------|
| Not processing files | Ensure files are in `/Needs_Action` |
| Exiting early | Use Ralph Wiggum loop for multi-step |
| MCP not connecting | Check `mcp.json` configuration |

---

## Security Notes

### Credentials

- `credentials.json` - Gmail OAuth2 (project root)
- `token.json` - Gmail auth token (auto-created)
- `~/.linkedin_session/` - LinkedIn session (auto-created)

**Never commit these files to git!**

### Rate Limiting

| Action | Limit |
|--------|-------|
| Gmail API calls | 100 per 120 seconds |
| LinkedIn checks | 1 per 5 minutes |
| Email sends | Max 50 per day (via MCP) |

---

## Next Steps (Gold Tier)

To upgrade to Gold Tier:

1. **Odoo Accounting Integration**
   - Install Odoo Community
   - Add Odoo MCP server
   - Auto-log transactions

2. **More Watchers**
   - WhatsApp Watcher
   - Finance/Bank Watcher
   - Twitter/X Watcher

3. **Advanced Features**
   - Weekly accounting audit
   - Error recovery
   - Comprehensive logging

---

## Resources

- **Hackathon Document:** `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- **Quick Start:** `SILVER_TIER_QUICKSTART.md`
- **Skill Docs:** `.agents/skills/*/SKILL.md`
- **Qwen Code Docs:** https://qwen-code.github.io/

---

*Built with Qwen Code + Obsidian + Python*
*Tier: Silver (Functional Assistant)*
