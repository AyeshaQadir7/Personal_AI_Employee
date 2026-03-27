---
name: email-mcp-server
description: |
  Model Context Protocol (MCP) server for sending emails via Gmail API.
  Provides tools for sending, drafting, and searching emails. Integrates with
  the AI Employee approval workflow - sensitive emails require human approval
  before sending.
---

# Email MCP Server

MCP server for email operations via Gmail API.

## Features

- **send_email**: Send emails with attachments
- **draft_email**: Create draft emails (no send)
- **search_emails**: Search Gmail with queries
- **mark_read**: Mark emails as read
- **list_labels**: Get Gmail labels/folders

## Setup

### 1. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select project
3. Enable **Gmail API**: `APIs & Services > Library > Gmail API`
4. Create OAuth2 credentials: `APIs & Services > Credentials > OAuth Client ID`
5. Download `credentials.json` to project root

### 2. Install Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 3. Start the Server

```bash
# Start Email MCP server
python .agents/skills/email-mcp-server/scripts/email_mcp_server.py

# With custom port
python .agents/skills/email-mcp-server/scripts/email_mcp_server.py --port 8809
```

### 4. Configure Claude Code

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "email",
      "command": "python",
      "args": ["/path/to/email_mcp_server.py"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/path/to/credentials.json"
      }
    }
  ]
}
```

## Usage

### Send Email

```python
# Via MCP client
python scripts/mcp-client.py call -u http://localhost:8809 -t send_email \
  -p '{
    "to": "client@example.com",
    "subject": "Invoice #123",
    "body": "Please find attached your invoice.",
    "attachments": ["/path/to/invoice.pdf"]
  }'
```

### Draft Email (No Send)

```python
python scripts/mcp-client.py call -u http://localhost:8809 -t draft_email \
  -p '{
    "to": "client@example.com",
    "subject": "Invoice #123",
    "body": "Please find attached your invoice."
  }'
```

### Search Emails

```python
python scripts/mcp-client.py call -u http://localhost:8809 -t search_emails \
  -p '{
    "query": "is:unread from:client@example.com",
    "max_results": 10
  }'
```

## Human-in-the-Loop Pattern

For sensitive emails, use the approval workflow:

1. **Claude drafts email** → Creates approval file in `/Pending_Approval/`
2. **Human reviews** → Moves file to `/Approved/`
3. **Orchestrator triggers MCP** → Email MCP sends the email
4. **Log action** → Move to `/Done/`

### Approval File Format

```markdown
---
type: approval_request
action: send_email
to: client@example.com
subject: Invoice #123
body: Please find attached...
attachment: /Vault/Invoices/2026-01_Client_A.pdf
created: 2026-01-07T10:30:00Z
status: pending
---

## Email Details
- **To:** client@example.com
- **Subject:** Invoice #123
- **Attachment:** invoice.pdf

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.
```

## Tools Reference

| Tool | Description | Requires Approval |
|------|-------------|-------------------|
| `send_email` | Send email | Yes (new contacts, bulk) |
| `draft_email` | Create draft | No |
| `search_emails` | Search Gmail | No |
| `mark_read` | Mark as read | No |
| `list_labels` | Get labels | No |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `credentials.json not found` | Download from Google Cloud Console |
| `Authentication failed` | Delete token.json and re-authenticate |
| `Rate limit exceeded` | Wait 1 hour or increase quota |
| `Attachment not found` | Use absolute path |

## Security Notes

- **Never commit** credentials or tokens
- Rotate OAuth credentials monthly
- Use test Gmail account for development
- Log all sent emails for audit
