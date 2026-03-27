# 🚀 Silver Tier Quick Start Guide

> **For Qwen Code Users** - Get your AI Employee's Silver Tier running in 15 minutes

This guide helps you activate the **Gmail Watcher** and **LinkedIn Watcher** with your existing `credentials.json`.

---

## ✅ Prerequisites Check

- [ ] Bronze Tier working (Filesystem Watcher + Orchestrator running)
- [ ] `credentials.json` in project root (`E:\personal_ai_employee\credentials.json`)
- [ ] Python 3.13+ installed
- [ ] Obsidian vault open at `AI_Employee_Vault/`

---

## Step 1: Install Dependencies

```bash
cd E:\personal_ai_employee

# Install Gmail API dependencies
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Install Playwright for LinkedIn
pip install playwright
playwright install chromium
```

**Verify Installation:**
```bash
python -c "from googleapiclient.discovery import build; print('✓ Gmail API OK')"
python -c "from playwright.sync_api import sync_playwright; print('✓ Playwright OK')"
```

---

## Step 2: Activate Gmail Watcher

### 2.1 First-Time Authentication

```bash
# This will open a browser for OAuth2 consent
python src/gmail_watcher.py AI_Employee_Vault
```

**What happens:**
1. Browser opens automatically
2. Sign in with your Google account
3. Grant Gmail API permissions
4. `token.json` is created (saved for future runs)
5. Press `Ctrl+C` to stop after authentication

### 2.2 Start Gmail Watcher

Open a **new terminal** and run:

```bash
# Terminal 2: Gmail Watcher
python src/gmail_watcher.py AI_Employee_Vault --interval 120
```

**Expected output:**
```
============================================================
📧 Gmail Watcher Started
============================================================
   Vault: AI_Employee_Vault
   Check Interval: 120s
   Credentials: credentials.json

📬 Watching for new unread emails...
   Action files will be created in: AI_Employee_Vault/Needs_Action
```

### 2.3 Test Gmail Watcher

1. **Send yourself a test email** with subject: `Test Invoice Request`
2. **Wait 2 minutes** (check interval)
3. **Check** `AI_Employee_Vault/Needs_Action/` for new `EMAIL_*.md` file

---

## Step 3: Activate LinkedIn Watcher

### 3.1 First-Time Login

```bash
# This opens browser for manual LinkedIn login
python src/linkedin_watcher.py AI_Employee_Vault --login --no-headless
```

**What happens:**
1. Browser opens to LinkedIn login page
2. Login with your LinkedIn credentials
3. Session saved to `~/.linkedin_session/`
4. Press `Ctrl+C` after login completes

### 3.2 Start LinkedIn Watcher

Open **another terminal** and run:

```bash
# Terminal 3: LinkedIn Watcher
python src/linkedin_watcher.py AI_Employee_Vault --interval 300 --no-headless
```

**Expected output:**
```
============================================================
💼 LinkedIn Watcher Started
============================================================
   Vault: AI_Employee_Vault
   Check Interval: 300s
   Session: C:\Users\your_name\.linkedin_session

💼 Watching for business opportunities...
```

### 3.3 Test LinkedIn Watcher

The LinkedIn Watcher detects:
- Connection requests with business keywords (hiring, freelance, project)
- Messages about opportunities
- Posts mentioning "looking for", "need help", "recommend"

**Note:** LinkedIn monitoring is passive - it waits for relevant activity. You can:
- Send yourself a connection request from another account
- Or wait for organic activity

---

## Step 4: Verify Orchestrator

Ensure the Orchestrator is running in a **separate terminal**:

```bash
# Terminal 4: Orchestrator
python src/orchestrator.py AI_Employee_Vault
```

**What it does:**
- Monitors `/Needs_Action` for new files from watchers
- Creates plan files in `/Plans`
- Moves files to `/In_Progress` for Qwen Code processing

---

## Step 5: Process with Qwen Code

When action files appear in `/Needs_Action`:

```bash
# Navigate to vault
cd AI_Employee_Vault

# Start Qwen Code
qwen

# In Qwen session:
"Process all files in /Needs_Action folder. Create plans and follow Company_Handbook rules."
```

### Ralph Wiggum Loop (Multi-Step Tasks)

For complex processing:

```bash
qwen
/ralph-loop "Process all emails in /Needs_Action, create response drafts, move to /Done when complete" --max-iterations 5
```

---

## Running All Components

You need **4 terminals** running simultaneously:

| Terminal | Command | Purpose |
|----------|---------|---------|
| 1 | `python src/gmail_watcher.py AI_Employee_Vault --interval 120` | Gmail monitoring |
| 2 | `python src/linkedin_watcher.py AI_Employee_Vault --interval 300` | LinkedIn monitoring |
| 3 | `python src/orchestrator.py AI_Employee_Vault` | Task orchestration |
| 4 | `qwen` (in vault directory) | AI reasoning |

---

## Troubleshooting

### Gmail Watcher Issues

| Problem | Solution |
|---------|----------|
| `credentials.json not found` | Ensure file is at `E:\personal_ai_employee\credentials.json` |
| Browser doesn't open | Run with `--login` flag manually |
| `token.json expired` | Delete `token.json` and re-authenticate |
| No emails detected | Check Gmail has unread messages |

### LinkedIn Watcher Issues

| Problem | Solution |
|---------|----------|
| Login required every time | Ensure `--login` completed successfully |
| Browser crashes | Increase interval: `--interval 600` |
| No activities detected | LinkedIn activity is passive - wait for real activity |
| Session not saving | Check write permissions to `~/.linkedin_session/` |

### Orchestrator Issues

| Problem | Solution |
|---------|----------|
| Files not moving | Check file permissions in vault |
| Dashboard not updating | Verify `Dashboard.md` exists |

---

## Silver Tier Features Active

Once running, you have:

| Feature | Status | Description |
|---------|--------|-------------|
| 📧 Gmail Watcher | ✅ Active | Monitors unread emails |
| 💼 LinkedIn Watcher | ✅ Active | Detects business opportunities |
| 📁 Filesystem Watcher | ✅ Active | Watches Inbox folder |
| 🎵 Orchestrator | ✅ Active | Manages task flow |
| 🔄 Qwen Code | ⏳ Ready | AI reasoning (manual trigger) |

---

## Next Steps

1. **Monitor for 24 hours** - Let watchers collect real activity
2. **Review action files** - Check `/Needs_Action` quality
3. **Process with Qwen** - Run Qwen Code sessions regularly
4. **Tune keywords** - Adjust watcher sensitivity in source files
5. **Add more watchers** - WhatsApp, Finance, etc.

---

## Daily Workflow

### Morning (9:00 AM)
```bash
# Start all watchers
# Check Dashboard.md for overnight activity
# Process any files in /Needs_Action with Qwen
```

### Evening (6:00 PM)
```bash
# Review /Pending_Approval folder
# Approve/reject pending actions
# Check logs in /Logs/
```

---

**Need Help?** Check individual skill documentation:
- Gmail Watcher: `.agents/skills/gmail-watcher/SKILL.md`
- LinkedIn Watcher: `.agents/skills/linkedin-watcher/SKILL.md`
- HITL Workflow: `.agents/skills/hitl-approval-workflow/SKILL.md`
