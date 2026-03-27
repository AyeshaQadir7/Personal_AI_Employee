---
name: gmail-watcher
description: |
  Monitor Gmail for new unread messages and create action files in Obsidian vault.
  Uses Gmail API with OAuth2 authentication. Watches for important/unread emails
  and triggers AI processing for invoices, urgent messages, and client communications.
---

# Gmail Watcher

Monitor Gmail inbox and create actionable files for Claude to process.

## Setup

### 1. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Gmail API**: `APIs & Services > Library > Gmail API`
4. Create OAuth2 credentials: `APIs & Services > Credentials > OAuth Client ID`
5. Download `credentials.json` to project root

### 2. Install Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 3. First-Time Authentication

Run the watcher - it will open a browser window for OAuth2 consent. This creates a `token.json` file for future runs.

## Usage

```bash
# Start Gmail Watcher
python .agents/skills/gmail-watcher/scripts/gmail_watcher.py AI_Employee_Vault

# With custom check interval (default: 120 seconds)
python .agents/skills/gmail-watcher/scripts/gmail_watcher.py AI_Employee_Vault --interval 60

# Dry run mode (no action files created)
python .agents/skills/gmail-watcher/scripts/gmail_watcher.py AI_Employee_Vault --dry-run
```

## Configuration

Create `.env` file in project root:

```env
# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json

# Watcher Configuration
GMAIL_CHECK_INTERVAL=120
GMAIL_LABEL_FILTER=IMPORTANT
GMAIL_MAX_RESULTS=50
```

## How It Works

1. **Polls Gmail** every 120 seconds (configurable) for unread/important messages
2. **Extracts metadata**: sender, subject, snippet, attachments
3. **Creates action file** in `/Needs_Action/` with email content
4. **Tracks processed emails** to avoid duplicates
5. **Saves state** to `.state_GmailWatcher.txt` for persistence

## Action File Format

```markdown
---
type: email
from: client@example.com
subject: Invoice Request - January 2026
received: 2026-01-07T10:30:00Z
priority: high
status: pending
message_id: 18d4f2a3b5c6e7f8
---

# Email: Invoice Request - January 2026

## Sender
client@example.com

## Received
2026-01-07 10:30 AM

## Content
Hi, can you send me the invoice for January services?

## Attachments
None

## Suggested Actions
- [ ] Extract invoice details (amount, due date, vendor)
- [ ] Log in accounting tracker
- [ ] Schedule payment if approved
- [ ] Move to /Done when complete
```

## Keyword Detection

The watcher flags emails containing these keywords as **high priority**:

| Keyword | Action |
|---------|--------|
| invoice, payment, bill | Create invoice action |
| urgent, asap, emergency | Flag for immediate attention |
| help, support | Queue for response |
| contract, agreement | Create review task |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `credentials.json not found` | Download from Google Cloud Console |
| `token.json expired` | Delete token.json and re-authenticate |
| `No messages found` | Check Gmail API is enabled |
| `Rate limit exceeded` | Increase check interval to 300+ seconds |
| `Permission denied` | Ensure Gmail API scope includes `gmail.readonly` |

## Security Notes

- **Never commit** `credentials.json` or `token.json` to git
- Store credentials in environment variables for production
- Rotate OAuth credentials monthly
- Use test Gmail account for development

## Integration with Orchestrator

When Gmail Watcher creates an action file:
1. Orchestrator detects file in `/Needs_Action`
2. Moves to `/In_Progress`
3. Creates plan file in `/Plans`
4. Triggers Claude Code for processing
5. Claude drafts response or creates approval request

## Example Flow

```
Gmail (new email) 
  → Gmail Watcher 
  → /Needs_Action/EMAIL_18d4f2a3b5c6e7f8.md
  → Orchestrator 
  → /In_Progress/
  → Claude Code processes
  → /Pending_Approval/ (if action needed)
  → Human approves
  → /Approved/
  → Email MCP sends reply
  → /Done/
```
