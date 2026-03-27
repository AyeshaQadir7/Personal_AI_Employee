# 🚀 Silver Tier Setup - Without Playwright

> **Recommended Approach** - Works with Python 3.14, no Playwright needed!

This guide sets up **90% of Silver Tier functionality** using Gmail API + Email notifications.

---

## Architecture (No Playwright)

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT                           │
│  Dashboard.md | Company_Handbook.md | /Needs_Action         │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    QWEN CODE (Brain)                        │
└─────────────────────────────────────────────────────────────┘
                    ↕                        ↕
┌──────────────────────┐          ┌───────────────────────────┐
│   WATCHERS (Senses)  │          │   MCP SERVERS (Hands)     │
│  ✅ Gmail Watcher    │          │  📧 Email MCP (pending)   │
│  ✅ Filesystem       │          │  🌐 Browser MCP (later)   │
│  📧 Email-based      │          │                           │
│     LinkedIn/WhatsApp│          │                           │
└──────────────────────┘          └───────────────────────────┘
```

---

## Step 1: Install Dependencies

```bash
cd E:\personal_ai_employee

# Install Gmail API dependencies
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**Verify Installation:**
```bash
python -c "from googleapiclient.discovery import build; print('✓ Gmail API OK')"
```

---

## Step 2: Configure LinkedIn Email Notifications

Since we're not using Playwright, we'll catch LinkedIn activity via email:

### LinkedIn Settings

1. Go to **LinkedIn.com**
2. Click your profile picture → **Settings & Privacy**
3. Go to **Notifications** → **Email notifications**
4. Enable these:
   - ✅ **Messages** - Get email when you receive a message
   - ✅ **Connection requests** - Get email for new connection requests
   - ✅ **Post mentions** - Get email when mentioned in a post
   - ✅ **Comments on your posts** - Engagement notifications

### WhatsApp Settings (Optional)

1. Open WhatsApp → Settings
2. Enable **Email chat history** or use WhatsApp email digest

---

## Step 3: First-Time Gmail Authentication

```bash
# This will open a browser for OAuth2 consent
python src/gmail_watcher.py AI_Employee_Vault
```

**What happens:**
1. Browser opens automatically
2. Sign in with your Google account (the one with LinkedIn notifications)
3. Grant Gmail API permissions
4. `token.json` is created in project root
5. Press `Ctrl+C` to stop

---

## Step 4: Start All Watchers

Open **3 terminals**:

### Terminal 1: Gmail Watcher
```bash
cd E:\personal_ai_employee
python src/gmail_watcher.py AI_Employee_Vault --interval 120
```

### Terminal 2: Filesystem Watcher
```bash
cd E:\personal_ai_employee
python src/filesystem_watcher.py AI_Employee_Vault --interval 5
```

### Terminal 3: Orchestrator
```bash
cd E:\personal_ai_employee
python src/orchestrator.py AI_Employee_Vault
```

**Expected Output:**

**Terminal 1 (Gmail):**
```
============================================================
📧 Gmail Watcher Started
============================================================
   Vault: AI_Employee_Vault
   Check Interval: 120s

📬 Watching for new unread emails...
```

**Terminal 2 (Filesystem):**
```
============================================================
📁 Filesystem Watcher Started
============================================================
   Vault: AI_Employee_Vault
   Check Interval: 5s

💡 Drop files into: AI_Employee_Vault/Inbox
```

**Terminal 3 (Orchestrator):**
```
============================================================
🎵 AI Employee Orchestrator Started
============================================================
   Vault: AI_Employee_Vault
   Check Interval: 30s

📁 Monitoring folders:
   - /Needs_Action
   - /Approved
```

---

## Step 5: Test the System

### Test 1: Gmail Watcher

1. **Send yourself a test email** from another account:
   - Subject: `Test Invoice Request`
   - Body: `Hi, can you send me the invoice for January services?`

2. **Wait 2 minutes** (Gmail Watcher check interval)

3. **Check** `AI_Employee_Vault/Needs_Action/` for new file:
   ```
   EMAIL_Test_Invoice_Request_20260323_*.md
   ```

### Test 2: LinkedIn Email → Gmail Watcher

1. **Ask a friend to send you a LinkedIn message** or connection request

2. **Wait for email notification** from LinkedIn

3. **Mark email as unread** in Gmail (or it won't be detected)

4. **Wait 2 minutes**

5. **Check** `AI_Employee_Vault/Needs_Action/` for LinkedIn email

### Test 3: Filesystem Watcher

1. **Drop a file** into `AI_Employee_Vault/Inbox/`

2. **Wait 5 seconds**

3. **Check** `AI_Employee_Vault/Needs_Action/` for action file

---

## Step 6: Process with Qwen Code

When action files appear in `/Needs_Action`:

```bash
cd AI_Employee_Vault
qwen

# In Qwen session:
"Process all files in /Needs_Action folder. 
 Follow Company_Handbook.md rules.
 Create response drafts for emails.
 Move completed items to /Done."
```

### Ralph Wiggum Loop (Multi-Step Tasks)

```bash
qwen
/ralph-loop "Process all emails, create response drafts, move to /Done when complete" --max-iterations 5
```

---

## What You Get (Without Playwright)

| Feature | Status | How It Works |
|---------|--------|--------------|
| 📧 Gmail Monitoring | ✅ Full | Gmail API |
| 📁 File Drop | ✅ Full | Filesystem Watcher |
| 💼 LinkedIn Opportunities | ✅ Via Email | LinkedIn sends email notifications |
| 💬 WhatsApp Messages | ⚠️ Limited | Email digests or manual |
| 📤 Email Sending | ⏳ Pending | Email MCP (needs setup) |
| 📅 Scheduling | ✅ Full | Task Scheduler / cron |
| ✅ HITL Workflow | ✅ Full | File-based approval |

---

## Email Templates Gmail Watcher Detects

### LinkedIn Emails (Auto-Detected)

| Email Type | Subject Pattern | Priority |
|------------|-----------------|----------|
| Connection Request | "wants to connect on LinkedIn" | Medium |
| New Message | "You have a new message on LinkedIn" | High |
| Post Mention | "mentioned you in a post" | Medium |
| Job Alert | "Job alert: [position]" | Low |

### Business Emails (Auto-Detected)

| Email Type | Keywords | Priority |
|------------|----------|----------|
| Invoice Request | invoice, bill, payment | High |
| Client Inquiry | project, contract, freelance | High |
| Meeting Request | meeting, schedule, zoom | Medium |
| Newsletter | newsletter, subscribe | Low (auto-archive) |

---

## Daily Workflow

### Morning (9:00 AM)

```bash
# 1. Check Dashboard.md
# Open AI_Employee_Vault/Dashboard.md in Obsidian

# 2. Review overnight emails
# Check /Needs_Action folder

# 3. Process with Qwen Code
cd AI_Employee_Vault
qwen
"Process overnight emails and create action plans"
```

### Evening (6:00 PM)

```bash
# 1. Review /Pending_Approval
# Approve or reject pending actions

# 2. Check /Done folder
# Review what was accomplished

# 3. Check logs
# AI_Employee_Vault/Logs/
```

---

## Troubleshooting

### Gmail Watcher Not Detecting Emails

| Issue | Solution |
|-------|----------|
| No action files created | Check emails are **unread** |
| `token.json expired` | Delete `token.json` and re-authenticate |
| Only seeing some emails | Check Gmail filters/labels |

### LinkedIn Emails Not Detected

| Issue | Solution |
|-------|----------|
| No LinkedIn emails | Enable email notifications in LinkedIn settings |
| Emails auto-archived | Check Gmail filters |
| Marked as read automatically | Disable "mark as read" in LinkedIn settings |

### Orchestrator Issues

| Issue | Solution |
|-------|----------|
| Files not moving | Check file permissions |
| Dashboard not updating | Verify `Dashboard.md` exists |

---

## Upgrade Path (Later)

When you want full LinkedIn/WhatsApp integration:

### Option 1: Install Python 3.13 + Playwright
```bash
# Install Python 3.13 from python.org
py -3.13 -m venv venv
venv\Scripts\activate
pip install playwright
playwright install chromium
```

### Option 2: Use Official APIs
- WhatsApp Business API
- LinkedIn API (limited access)

### Option 3: Continue Email-Based
- Works well for most use cases
- No browser automation issues
- More reliable long-term

---

## Silver Tier Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| ✅ 2+ Watchers | Done | Gmail + Filesystem |
| ✅ LinkedIn monitoring | Done | Via email notifications |
| ✅ MCP server | ⏳ Pending | Email MCP (optional) |
| ✅ HITL workflow | Done | File-based |
| ✅ Scheduler | Done | Task Scheduler |
| ✅ Qwen Code integration | Done | Via orchestrator |

---

## Quick Reference Commands

```bash
# Start Gmail Watcher
python src/gmail_watcher.py AI_Employee_Vault --interval 120

# Start Filesystem Watcher
python src/filesystem_watcher.py AI_Employee_Vault --interval 5

# Start Orchestrator
python src/orchestrator.py AI_Employee_Vault

# Process with Qwen
cd AI_Employee_Vault
qwen

# Re-authenticate Gmail
del token.json
python src/gmail_watcher.py AI_Employee_Vault
```

---

**You're all set!** This setup catches 90% of business opportunities via email notifications without the complexity of browser automation.

*Tagline: Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*
