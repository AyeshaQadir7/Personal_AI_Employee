# Silver Tier Setup Guide

> **Functional Assistant** - Estimated setup time: 2-3 hours

This guide walks you through setting up all Silver Tier features for your AI Employee.

## Silver Tier Requirements Checklist

From the hackathon document:

- [x] All Bronze requirements (COMPLETE)
- [ ] Two or more Watcher scripts (Gmail + WhatsApp)
- [ ] Automatically Post on LinkedIn about business
- [ ] Claude reasoning loop that creates Plan.md files
- [ ] One working MCP server for external action (email)
- [ ] Human-in-the-loop approval workflow
- [ ] Basic scheduling via cron or Task Scheduler
- [ ] All AI functionality as Agent Skills

## Prerequisites

Ensure Bronze Tier is working:
- [ ] Obsidian vault open and functional
- [ ] Filesystem Watcher running
- [ ] Orchestrator running
- [ ] Files process from Inbox → Needs_Action → Done

## Step 1: Install Dependencies

### Python Dependencies

```bash
# Navigate to project root
cd E:\personal_ai_employee

# Install Silver Tier dependencies
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install playwright
playwright install chromium
```

### Verify Installation

```bash
# Check Google API client
python -c "from googleapiclient.discovery import build; print('✓ Google API OK')"

# Check Playwright
python -c "from playwright.sync_api import sync_playwright; print('✓ Playwright OK')"
```

## Step 2: Setup Gmail Watcher

### 2.1 Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project (or select existing)
3. Enable Gmail API:
   - Click `APIs & Services` → `Library`
   - Search for "Gmail API"
   - Click `Enable`

### 2.2 Create OAuth2 Credentials

1. Go to `APIs & Services` → `Credentials`
2. Click `+ CREATE CREDENTIALS` → `OAuth client ID`
3. Application type: `Web application`
4. Name: `Gmail Watcher`
5. Download `credentials.json`
6. Save to project root: `E:\personal_ai_employee\credentials.json`

### 2.3 First-Time Authentication

```bash
# Run Gmail Watcher (will open browser for OAuth consent)
python .agents/skills/gmail-watcher/scripts/gmail_watcher.py AI_Employee_Vault

# A browser window will open
# 1. Sign in with your Google account
# 2. Grant permissions
# 3. Token saved to token.json
# 4. Press Ctrl+C to stop (first run is for auth only)
```

### 2.4 Start Gmail Watcher

```bash
# Start in background (Terminal 1)
python .agents/skills/gmail-watcher/scripts/gmail_watcher.py AI_Employee_Vault --interval 120
```

### 2.5 Test Gmail Watcher

1. Send yourself a test email with subject "Test Invoice"
2. Wait 2 minutes (check interval)
3. Check `AI_Employee_Vault/Needs_Action/` for new EMAIL_*.md file

## Step 3: Setup WhatsApp Watcher

### 3.1 First-Time Login

```bash
# Run with --login flag to scan QR code
python .agents/skills/whatsapp-watcher/scripts/whatsapp_watcher.py AI_Employee_Vault --login
```

1. Browser opens with WhatsApp Web QR code
2. Scan with your WhatsApp mobile app:
   - Open WhatsApp on phone
   - Settings → Linked Devices → Link a Device
   - Scan QR code
3. Session saved to `~/.whatsapp_session/`

### 3.2 Start WhatsApp Watcher

```bash
# Start in background (Terminal 2)
python .agents/skills/whatsapp-watcher/scripts/whatsapp_watcher.py AI_Employee_Vault --interval 60
```

### 3.3 Test WhatsApp Watcher

1. Send yourself a WhatsApp message with "urgent invoice"
2. Wait 1 minute
3. Check `AI_Employee_Vault/Needs_Action/` for new WHATSAPP_*.md file

## Step 4: Setup Email MCP Server

### 4.1 Update Gmail API Scopes

The Email MCP server needs additional scopes. Re-authenticate:

```bash
# Delete old token
del token.json

# Run Email MCP server (will re-authenticate with full scopes)
python .agents/skills/email-mcp-server/scripts/email_mcp_server.py
```

### 4.2 Configure Claude Code MCP

Edit `~/.config/claude-code/mcp.json`:

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
    }
  ]
}
```

### 4.3 Test Email MCP

```bash
# Test send (will fail without approval - expected!)
# This verifies the server is running
python .agents/skills/browsing-with-playwright/scripts/mcp-client.py call \
  -u http://localhost:8809 \
  -t send_email \
  -p '{"to": "test@example.com", "subject": "Test", "body": "Test email"}'
```

## Step 5: Setup LinkedIn MCP Server

### 5.1 Start LinkedIn MCP Server

```bash
# Start LinkedIn MCP (will open browser for login)
python .agents/skills/linkedin-mcp-server/scripts/linkedin_mcp_server.py --no-headless
```

1. Browser opens to LinkedIn login
2. Login to your LinkedIn account
3. Session saved to `~/.linkedin_session/`
4. Press Ctrl+C to stop

### 5.2 Configure in Claude Code

Update `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    ...existing servers...,
    {
      "name": "linkedin",
      "command": "python",
      "args": ["E:\\personal_ai_employee\\.agents\\skills\\linkedin-mcp-server\\scripts\\linkedin_mcp_server.py"]
    }
  ]
}
```

## Step 6: Setup Scheduler

### Windows Task Scheduler

```bash
# Install scheduled tasks
python .agents/skills/scheduler/scripts/scheduler_windows.py setup
```

This creates:
- **Daily Briefing**: 8:00 AM every day
- **Weekly Audit**: Sunday 10:00 PM
- **Monthly Subscription Audit**: 1st of month at 9:00 AM

### Verify Tasks

```bash
# List installed tasks
python .agents/skills/scheduler/scripts/scheduler_windows.py list
```

### Test Scheduled Task Manually

```bash
# Run daily briefing manually
python src/orchestrator.py AI_Employee_Vault --scheduled-task daily_briefing

# Check output in AI_Employee_Vault/Briefings/
```

## Step 7: Verify HITL Workflow

### Test Approval Flow

1. **Create test approval file**:

```markdown
---
type: approval_request
action: send_email
to: test@example.com
subject: Test Approval
created: 2026-01-07T10:30:00Z
status: pending
---

## Test Email
This is a test approval request.

## To Approve
Move to /Approved folder.
```

2. **Save to** `AI_Employee_Vault/Pending_Approval/TEST_APPROVAL.md`

3. **Verify Orchestrator detects it**:
   - Check orchestrator logs
   - File should be processed when moved to /Approved

## Step 8: Setup Ralph Wiggum Loop

### Enable in Claude Code

When running Claude Code for multi-step tasks:

```bash
claude

# In Claude session:
/ralph-loop "Process all files in /Needs_Action and move to /Done" \
  --max-iterations 10
```

### Verify Ralph Hook

1. Check `.claude/plugins/RALPH_WIGGUM.md` exists
2. Review completion criteria
3. Test with simple task first

## Step 9: Update requirements.txt

The project now needs these dependencies:

```txt
# Silver Tier Dependencies
google-api-python-client>=2.100.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=1.1.0
playwright>=1.40.0

# Optional: APScheduler for Python-based scheduling
# APScheduler>=3.10.0
```

## Step 10: Full System Test

### End-to-End Flow Test

1. **Gmail Test**:
   - Send email with "invoice request"
   - Wait for Gmail Watcher to detect
   - Verify action file created
   - Claude processes and creates draft
   - Approval file created in /Pending_Approval

2. **WhatsApp Test**:
   - Send WhatsApp with "urgent payment"
   - Wait for WhatsApp Watcher
   - Verify action file created
   - Claude processes

3. **LinkedIn Test**:
   - Claude drafts LinkedIn post
   - Creates approval file
   - Human moves to /Approved
   - LinkedIn MCP publishes

4. **Scheduler Test**:
   - Wait for scheduled time OR run manually
   - Check briefing generated in /Briefings/

## Troubleshooting

### Gmail Watcher Issues

| Issue | Solution |
|-------|----------|
| `credentials.json not found` | Download from Google Cloud Console |
| `token.json expired` | Delete and re-authenticate |
| No emails detected | Check Gmail API enabled |

### WhatsApp Watcher Issues

| Issue | Solution |
|-------|----------|
| QR code every time | Session not saving - check permissions |
| No messages detected | Ensure WhatsApp Web loaded |
| Browser crashes | Increase interval to 60+ seconds |

### MCP Server Issues

| Issue | Solution |
|-------|----------|
| Server not connecting | Check process running: `pgrep -f mcp` |
| Authentication failed | Re-run with fresh credentials |
| Rate limited | Wait 1 hour or increase quota |

### Scheduler Issues

| Issue | Solution |
|-------|----------|
| Task not running | Check Task Scheduler history |
| Python not found | Use absolute path in task config |
| Permission denied | Run as appropriate user |

## Silver Tier Complete! ✅

You now have:
- ✅ **Gmail Watcher** - Monitors inbox for important emails
- ✅ **WhatsApp Watcher** - Detects urgent messages
- ✅ **Email MCP Server** - Sends emails (with approval)
- ✅ **LinkedIn MCP Server** - Posts updates (with approval)
- ✅ **HITL Workflow** - Human approval for sensitive actions
- ✅ **Scheduler** - Daily briefings, weekly audits
- ✅ **Ralph Wiggum Loop** - Multi-step task persistence

### Next Steps

1. **Monitor for 24 hours** - Ensure watchers run continuously
2. **Review logs** - Check `AI_Employee_Vault/Logs/` daily
3. **Tune keywords** - Adjust watcher sensitivity
4. **Add more MCP servers** - Calendar, Slack, etc.
5. **Upgrade to Gold Tier** - Add Odoo accounting integration

## Daily Operations

### Morning Checklist

- [ ] Check Dashboard.md for overnight activity
- [ ] Review /Needs_Action folder
- [ ] Approve pending items in /Pending_Approval
- [ ] Review daily briefing (if scheduled)

### Weekly Checklist

- [ ] Review /Rejected items for patterns
- [ ] Audit /Logs for anomalies
- [ ] Check watcher state files
- [ ] Review weekly briefing

---

*For detailed documentation on each skill, see the SKILL.md files in each skill directory.*
