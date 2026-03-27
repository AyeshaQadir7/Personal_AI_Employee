---
name: whatsapp-watcher
description: |
  Monitor WhatsApp Web for new messages containing urgent keywords.
  Uses Playwright for browser automation. Detects messages with keywords
  like 'urgent', 'invoice', 'payment', 'help' and creates action files.
  WARNING: Respect WhatsApp's Terms of Service - use for personal/business
  automation only, not for spam or bulk messaging.
---

# WhatsApp Watcher

Monitor WhatsApp Web for urgent messages and create actionable files for Claude to process.

## ⚠️ Important Notice

**Terms of Service**: This tool uses WhatsApp Web automation. Ensure you:
- Only use for personal/business communication you're authorized to access
- Don't use for spam, bulk messaging, or commercial scraping
- Respect rate limits and WhatsApp's policies
- Understand that automated access may violate WhatsApp's ToS in some jurisdictions

## Setup

### 1. Install Playwright

```bash
pip install playwright
playwright install chromium
```

### 2. First-Time WhatsApp Web Login

```bash
# Run the watcher with --login flag
python .agents/skills/whatsapp-watcher/scripts/whatsapp_watcher.py AI_Employee_Vault --login
```

This opens a browser window. Scan the QR code with your WhatsApp mobile app. The session is saved for future runs.

## Usage

```bash
# Start WhatsApp Watcher
python .agents/skills/whatsapp-watcher/scripts/whatsapp_watcher.py AI_Employee_Vault

# Login mode (QR code scan)
python .agents/skills/whatsapp-watcher/scripts/whatsapp_watcher.py AI_Employee_Vault --login

# With custom check interval (default: 30 seconds)
python .agents/skills/whatsapp-watcher/scripts/whatsapp_watcher.py AI_Employee_Vault --interval 60

# Dry run mode
python .agents/skills/whatsapp-watcher/scripts/whatsapp_watcher.py AI_Employee_Vault --dry-run
```

## Configuration

Create `.env` file in project root:

```env
# WhatsApp Watcher Configuration
WHATSAPP_CHECK_INTERVAL=30
WHATSAPP_SESSION_PATH=/path/to/session
WHATSAPP_KEYWORDS=urgent,asap,invoice,payment,help
```

## How It Works

1. **Launches headless browser** with saved WhatsApp Web session
2. **Monitors chat list** for unread messages every 30 seconds
3. **Filters by keywords**: urgent, asap, invoice, payment, help
4. **Extracts message content** and sender info
5. **Creates action file** in `/Needs_Action/`
6. **Tracks processed messages** to avoid duplicates

## Keyword Detection

| Keyword | Priority | Action |
|---------|----------|--------|
| urgent, asap, emergency | High | Immediate flag |
| invoice, payment, bill | High | Create invoice action |
| help, support | Medium | Queue for response |
| thanks, ok, sure | Low | Ignore (acknowledgments) |

## Action File Format

```markdown
---
type: whatsapp
from: +1234567890 (Client Name)
received: 2026-01-07T10:30:00Z
priority: high
status: pending
chat_id: 1234567890@c.us
---

# WhatsApp Message

## Sender
+1234567890 (Client Name)

## Received
2026-01-07 10:30 AM

## Message
Hey, can you send me the invoice for January?

## Detected Keywords
- invoice
- payment

## Suggested Actions
- [ ] Extract invoice details (amount, due date, vendor)
- [ ] Log in accounting tracker
- [ ] Generate and send invoice
- [ ] Move to /Done when complete
```

## Session Management

Sessions are stored in `~/.whatsapp_session/`. To reset:

```bash
# Delete session and re-login
rm -rf ~/.whatsapp_session
python whatsapp_watcher.py AI_Employee_Vault --login
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| QR code shows every time | Session not saved - check write permissions |
| No messages detected | Ensure WhatsApp Web is loaded |
| Browser crashes | Increase check interval to 60+ seconds |
| "Unread" selector fails | WhatsApp Web UI changed - update selectors |
| Rate limited | Reduce frequency, respect ToS |

## Security Notes

- **Never commit** session files to git
- Session gives full access to your WhatsApp - protect it
- Use on personal device only
- Log out from WhatsApp Web when not in use

## Integration with Orchestrator

```
WhatsApp (new message)
  → WhatsApp Watcher (Playwright)
  → /Needs_Action/WHATSAPP_client_2026-01-07.md
  → Orchestrator
  → /In_Progress/
  → Claude Code processes
  → Drafts response
  → /Pending_Approval/
  → Human approves
  → WhatsApp MCP sends reply
  → /Done/
```

## Alternative: WhatsApp Business API

For production use, consider the official [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/):
- Official, ToS-compliant
- Webhook-based (no polling needed)
- Supports business verification
- Rate limits apply
