---
name: hitl-approval-workflow
description: |
  Human-in-the-Loop (HITL) approval workflow for sensitive AI actions.
  Provides file-based approval system where AI creates approval requests
  in /Pending_Approval, human moves to /Approved or /Rejected, and
  Orchestrator executes approved actions. Supports payments, emails,
  social posts, and other sensitive operations.
---

# Human-in-the-Loop (HITL) Approval Workflow

File-based approval system for sensitive AI actions.

## Overview

The HITL workflow ensures human oversight for sensitive operations:

```
┌─────────────┐    ┌──────────────────┐    ┌──────────┐    ┌──────────┐
│ AI detects  │    │ Creates approval │    │ Human    │    │ Execute  │
│ action need │───▶│ in /Pending_     │───▶│ reviews  │───▶│ & log    │
│             │    │ Approval/        │    │ & moves  │    │          │
└─────────────┘    └──────────────────┘    └──────────┘    └──────────┘
                                              │
                                              ▼
                                     ┌──────────────┐
                                     │ /Approved    │
                                     │ or /Rejected │
                                     └──────────────┘
```

## When to Use HITL

| Action Category | Auto-Approve | Requires Approval |
|-----------------|--------------|-------------------|
| Email replies   | Known contacts | New contacts, bulk |
| Payments        | < $50 recurring | All new payees, ≥ $100 |
| Social media    | Never | **All posts** |
| Contracts       | Never | **All legal docs** |
| File operations | Create, read | Delete, move outside vault |

## Approval File Format

### Payment Approval

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
bank_account: XXXX1234
reason: Invoice #1234 payment
due_date: 2026-01-15
created: 2026-01-07T10:30:00Z
expires: 2026-01-08T10:30:00Z
status: pending
---

# Payment Approval Request

## Details
- **Amount:** $500.00
- **Recipient:** Client A
- **Bank:** XXXX1234
- **Reference:** Invoice #1234
- **Due Date:** January 15, 2026

## Context
Payment for January 2026 services as per contract.

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder.

## To Request Changes
Edit this file and add comments in the Notes section.

---
*Created by AI Employee - Payment requires human approval*
```

### Email Send Approval

```markdown
---
type: approval_request
action: send_email
to: client@example.com
cc: manager@example.com
subject: Invoice #123 - January 2026
has_attachment: true
created: 2026-01-07T10:30:00Z
status: pending
---

# Email Send Approval Request

## Recipients
- **To:** client@example.com
- **CC:** manager@example.com

## Subject
Invoice #123 - January 2026

## Content
Dear Client,

Please find attached your invoice for January 2026 services...

## Attachments
- /Vault/Invoices/2026-01_Client_A.pdf

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder.

---
*Created by AI Employee - Email send requires human approval*
```

### LinkedIn Post Approval

```markdown
---
type: approval_request
action: linkedin_post
content: Excited to announce...
hashtags: AI, Automation, Startup
scheduled_time: 2026-01-08T09:00:00Z
created: 2026-01-07T10:30:00Z
status: pending
---

# LinkedIn Post Approval Request

## Content
Excited to announce our new AI Employee product! 
This has been in development for 3 months...

## Hashtags
#AI #Automation #Startup

## Scheduled Time
January 8, 2026 at 9:00 AM (optimal engagement time)

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder.

---
*Created by AI Employee - Social media post requires human approval*
```

## Workflow States

| Folder | Purpose | AI Action |
|--------|---------|-----------|
| `/Pending_Approval` | Awaiting human decision | Create approval files here |
| `/Approved` | Ready for execution | Execute and move to /Done |
| `/Rejected` | Declined by human | Log and archive |
| `/Done` | Completed | Archive for audit |

## Orchestrator Integration

The Orchestrator monitors `/Approved` folder:

```python
# In orchestrator.py
def _process_approved(self):
    approved_files = list(self.approved.glob('*.md'))
    
    for approved_file in approved_files:
        metadata = self._parse_frontmatter(approved_file.read_text())
        action_type = metadata.get('action')
        
        # Route to appropriate MCP server
        if action_type == 'send_email':
            self._execute_email_send(approved_file)
        elif action_type == 'payment':
            self._execute_payment(approved_file)
        elif action_type == 'linkedin_post':
            self._execute_linkedin_post(approved_file)
        
        # Move to Done
        approved_file.rename(self.done / approved_file.name)
```

## Approval Rules (Company Handbook)

Define rules in `Company_Handbook.md`:

```markdown
## Payment Authorization Thresholds

| Amount | Action |
|--------|--------|
| < $50 (recurring) | Auto-approve if payee exists |
| < $100 (one-time) | Draft + Notify |
| ≥ $100 | ❌ Requires explicit approval |
| New payee (any amount) | ❌ Requires explicit approval |

## Email Rules

| Scenario | Auto-Action | Requires Approval |
|----------|-------------|-------------------|
| Reply to known contact | Draft only | Send |
| Reply to new contact | ❌ | Draft + Send |
| Bulk send (>5 recipients) | ❌ | Always |
```

## Expiration and Reminders

Approval files can have expiration:

```markdown
---
expires: 2026-01-08T10:30:00Z
reminder_sent: false
---
```

The Orchestrator can send reminders for pending approvals:

```python
def _check_expiring_approvals(self):
    for approval_file in self.pending_approval.glob('*.md'):
        content = approval_file.read_text()
        metadata = self._parse_frontmatter(content)
        
        expires = metadata.get('expires')
        if expires and datetime.fromisoformat(expires) < datetime.now():
            # Create reminder
            self._notify_human(f"Approval expiring: {approval_file.name}")
```

## Audit Logging

All approvals are logged:

```json
{
  "timestamp": "2026-01-07T10:30:00Z",
  "action_type": "payment",
  "actor": "claude_code",
  "target": "Client A",
  "parameters": {"amount": 500.00},
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success"
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Approval not executed | Check file is in /Approved (not /Pending_Approval) |
| Wrong action taken | Review approval file metadata for accuracy |
| Duplicate execution | Check processed_ids in state file |
| Expired approval | Create new approval request |

## Best Practices

1. **Always include context** - Why is this action needed?
2. **Set clear deadlines** - When does this expire?
3. **Provide reject option** - What if human says no?
4. **Log everything** - Audit trail for compliance
5. **Test with dry-run** - Verify before real execution
